local key = KEYS[1]
local max_capacity = tonumber(ARGV[1])
local leak_rate = tonumber(ARGV[2])
local now = tonumber(ARGV[3])
local requested = tonumber(ARGV[4]) or 1

local data = redis.call("HMGET", key, "water", "last_leak")
local water = tonumber(data[1])
local last_leak = tonumber(data[2])

if water == nil or last_leak == nil then
    water = 0
    last_leak = now
else
    local delta = math.max(0, now - last_leak)
    water = math.max(0, water - delta * leak_rate)
    last_leak = now
end

local allowed = 0
local remaining = 0
local reset_after = 0

if (water + requested) <= max_capacity then
    allowed = 1
    water = water + requested
    remaining = math.floor(max_capacity - water)
    reset_after = 0
else
    allowed = 0
    remaining = 0
    local overflow = (water + requested) - max_capacity
    reset_after = overflow / leak_rate
end

local ttl = math.ceil(max_capacity / leak_rate) + 10
redis.call("HMSET", key, "water", water, "last_leak", last_leak)
redis.call("EXPIRE", key, ttl)

return {allowed, remaining, reset_after}
