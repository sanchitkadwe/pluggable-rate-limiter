import sys
import os
import time
import argparse
import asyncio

sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(__file__))))

import httpx
from rich.console import Console
from rich.table import Table
import uvicorn

console = Console()


def serve(host: str = "0.0.0.0", port: int = 8050, reload: bool = False):
    console.print(f"[bold green]Starting Rate Limiter Test Server on http://{host}:{port}[/bold green]")
    console.print(f"[bold cyan]Dashboard: http://localhost:{port}/dashboard[/bold cyan]")
    uvicorn.run("server.app:app", host=host, port=port, reload=reload)


async def run_load_test(
    url: str,
    method: str = "GET",
    total_requests: int = 15,
    concurrency: int = 1,
    delay: float = 0.1,
    header: str = None,
):
    console.print(f"[bold yellow]Sending {total_requests} '{method}' requests to {url}...[/bold yellow]")

    headers = {}
    if header:
        key, val = header.split(":", 1)
        headers[key.strip()] = val.strip()

    table = Table(title=f"Rate Limiter Load Test Results ({method} {url})")
    table.add_column("Req #", justify="right", style="cyan")
    table.add_column("Status Code", justify="center")
    table.add_column("Allowed", justify="center")
    table.add_column("Remaining", justify="right")
    table.add_column("Retry After", justify="right")
    table.add_column("Time (ms)", justify="right")

    allowed_count = 0
    blocked_count = 0

    async with httpx.AsyncClient(timeout=10.0) as client:
        for i in range(1, total_requests + 1):
            start = time.perf_counter()
            try:
                response = await client.request(method.upper(), url, headers=headers, json={"test": True} if method.upper() in ["POST", "PUT", "PATCH"] else None)

                elapsed_ms = (time.perf_counter() - start) * 1000.0

                remaining = response.headers.get("X-RateLimit-Remaining", "N/A")
                retry_after = response.headers.get("Retry-After", "-")

                if response.status_code == 200:
                    allowed_count += 1
                    status_fmt = f"[bold green]{response.status_code} OK[/bold green]"
                    allowed_fmt = "[green]YES[/green]"
                elif response.status_code == 429:
                    blocked_count += 1
                    status_fmt = f"[bold red]{response.status_code} TOO MANY[/bold red]"
                    allowed_fmt = "[red]NO (BLOCKED)[/red]"
                else:
                    status_fmt = f"[yellow]{response.status_code}[/yellow]"
                    allowed_fmt = "UNKNOWN"

                table.add_row(
                    str(i),
                    status_fmt,
                    allowed_fmt,
                    str(remaining),
                    str(retry_after),
                    f"{elapsed_ms:.1f}",
                )

            except Exception as e:
                table.add_row(str(i), "[bold red]ERROR[/bold red]", "ERR", "-", "-", "-")

            if delay > 0:
                await asyncio.sleep(delay)

    console.print(table)
    console.print(
        f"[bold]Summary:[/bold] Total: {total_requests} | "
        f"[green]Allowed: {allowed_count}[/green] | "
        f"[red]Blocked: {blocked_count}[/red]"
    )


def main():
    parser = argparse.ArgumentParser(description="Rate Limiter CLI")
    subparsers = parser.add_subparsers(dest="command")

    serve_parser = subparsers.add_parser("serve", help="Start the test server")
    serve_parser.add_argument("--host", default="0.0.0.0", help="Host to bind")
    serve_parser.add_argument("--port", type=int, default=8050, help="Port")

    test_parser = subparsers.add_parser("test", help="Run load test against target URL")
    test_parser.add_argument("--url", default="http://localhost:8050/api/data", help="Target URL")
    test_parser.add_argument("--method", default="GET", help="HTTP Method")
    test_parser.add_argument("-n", "--requests", type=int, default=15, help="Number of requests")
    test_parser.add_argument("--delay", type=float, default=0.1, help="Delay between requests in seconds")
    test_parser.add_argument("--header", help="Custom header e.g. 'X-API-Key: my-key'")

    args = parser.parse_args()

    if args.command == "serve":
        serve(host=args.host, port=args.port)
    elif args.command == "test":
        asyncio.run(
            run_load_test(
                url=args.url,
                method=args.method,
                total_requests=args.requests,
                delay=args.delay,
                header=args.header,
            )
        )
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
