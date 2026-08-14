local cur_key = KEYS[1]
local prev_key = KEYS[2]
local max_requests = tonumber(ARGV[1])
local window_seconds = tonumber(ARGV[2])
local time_into_cur = tonumber(ARGV[3])

local cur_count = tonumber(redis.call("GET", cur_key) or 0)
local prev_count = tonumber(redis.call("GET", prev_key) or 0)

local weight = (window_seconds - time_into_cur) / window_seconds
local estimated_count = prev_count * weight + cur_count

local allowed = 0
local remaining = 0
local reset_after = window_seconds - time_into_cur

if estimated_count < max_requests then
    redis.call("INCR", cur_key)
    redis.call("EXPIRE", cur_key, math.ceil(window_seconds * 2))
    allowed = 1
    remaining = math.max(0, math.floor(max_requests - (estimated_count + 1)))
else
    allowed = 0
    remaining = 0
end

return {allowed, remaining, reset_after}
