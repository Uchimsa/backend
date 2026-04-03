QUESTION

text: str
explanation: str
options: list[str]
right_option: int

TASK

text: str
explanation: str
options: list[str]
right_options: list[str]

CARD

text: str
explanation: str

AUTH

This backend does not implement its own signup/login endpoints. Users authenticate via Supabase Auth.

Flow:

1. Client signs up or logs in using Supabase Auth (SDK or REST).
2. Supabase returns an access token (JWT).
3. Client calls this API with header: Authorization: Bearer <access_token>.

Supabase Auth REST examples (replace {SUPABASE_URL} and {SUPABASE_ANON_KEY}):

Sign up:
curl -X POST "{SUPABASE_URL}/auth/v1/signup" \
 -H "apikey: {SUPABASE_ANON_KEY}" \
 -H "Content-Type: application/json" \
 -d '{"email":"user@example.com","password":"secret"}'

Log in:
curl -X POST "{SUPABASE_URL}/auth/v1/token?grant_type=password" \
 -H "apikey: {SUPABASE_ANON_KEY}" \
 -H "Content-Type: application/json" \
 -d '{"email":"user@example.com","password":"secret"}'

Then use the returned access token with this API:
curl -H "Authorization: Bearer <access_token>" \
 http://localhost:8000/api/v1/subjects
