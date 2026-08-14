local key = KEYS[1]
local max_requests = tonumber(ARGV[1])
local window_seconds = tonumber(ARGV[2])
local now = tonumber(ARGV[3])

local current_count = redis.call("INCRBY", key, 1)

if current_count == 1 then
    redis.call("EXPIRE", key, math.ceil(window_seconds))
end

local ttl = redis.call("TTL", key)
if ttl < 0 then
    ttl = window_seconds
end

local allowed = 0
local remaining = 0
local reset_after = ttl

if current_count <= max_requests then
    allowed = 1
    remaining = max_requests - current_count
else
    allowed = 0
    remaining = 0
end

return {allowed, remaining, reset_after}
