local key = KEYS[1]
local max_capacity = tonumber(ARGV[1])
local refill_rate = tonumber(ARGV[2])
local now = tonumber(ARGV[3])
local requested = tonumber(ARGV[4]) or 1

local data = redis.call("HMGET", key, "tokens", "last_updated")
local tokens = tonumber(data[1])
local last_updated = tonumber(data[2])

if tokens == nil or last_updated == nil then
    tokens = max_capacity
    last_updated = now
else
    local delta = math.max(0, now - last_updated)
    tokens = math.min(max_capacity, tokens + delta * refill_rate)
    last_updated = now
end

local allowed = 0
local remaining = tokens
local reset_after = 0

if tokens >= requested then
    allowed = 1
    tokens = tokens - requested
    remaining = tokens
    reset_after = 0
else
    allowed = 0
    remaining = tokens
    local needed = requested - tokens
    reset_after = needed / refill_rate
end

local ttl = math.ceil(max_capacity / refill_rate) + 10
redis.call("HMSET", key, "tokens", tokens, "last_updated", last_updated)
redis.call("EXPIRE", key, ttl)

return {allowed, math.floor(remaining), reset_after}
