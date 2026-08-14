local key = KEYS[1]
local max_requests = tonumber(ARGV[1])
local window_seconds = tonumber(ARGV[2])
local now = tonumber(ARGV[3])
local req_id = ARGV[4]

local window_start = now - window_seconds

redis.call("ZREMRANGEBYSCORE", key, "-inf", window_start)

local current_count = redis.call("ZCARD", key)

local allowed = 0
local remaining = 0
local reset_after = 0

if current_count < max_requests then
    redis.call("ZADD", key, now, req_id)
    allowed = 1
    remaining = max_requests - (current_count + 1)
    reset_after = window_seconds
else
    allowed = 0
    remaining = 0
    local oldest = redis.call("ZRANGE", key, 0, 0, "WITHSCORES")
    if oldest and #oldest >= 2 then
        local oldest_ts = tonumber(oldest[2])
        reset_after = math.max(0, (oldest_ts + window_seconds) - now)
    else
        reset_after = window_seconds
    end
end

redis.call("EXPIRE", key, math.ceil(window_seconds) + 5)

return {allowed, remaining, reset_after}
