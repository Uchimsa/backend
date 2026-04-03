create extension if not exists "pgcrypto";

create table if not exists subjects (
  id uuid primary key default gen_random_uuid(),
  name text not null,
  icon_name text
);

create table if not exists weeks (
  id uuid primary key default gen_random_uuid(),
  subject_id uuid not null references subjects(id) on delete cascade,
  week_number int not null,
  title text not null,
  unique (subject_id, week_number)
);

create table if not exists questions (
  id uuid primary key default gen_random_uuid(),
  week_id uuid not null references weeks(id) on delete cascade,
  type text not null check (type in ('flashcard', 'test', 'task')),
  question_text text not null,
  answer_text text,
  options jsonb,
  correct_option_index int,
  explanation text
);

create table if not exists users (
  id uuid primary key references auth.users(id) on delete cascade,
  full_name text,
  xp int not null default 0
);

create table if not exists user_subjects (
  user_id uuid not null references users(id) on delete cascade,
  subject_id uuid not null references subjects(id) on delete cascade,
  primary key (user_id, subject_id)
);

create table if not exists user_progress (
  id uuid primary key default gen_random_uuid(),
  user_id uuid not null references users(id) on delete cascade,
  question_id uuid not null references questions(id) on delete cascade,
  status text not null default 'new' check (status in ('new', 'learning', 'mastered')),
  is_known boolean,
  interval int not null default 0,
  ease_factor float not null default 2.5,
  views int not null default 0,
  unique (user_id, question_id)
);

create table if not exists study_plans (
  id uuid primary key default gen_random_uuid(),
  user_id uuid not null references users(id) on delete cascade,
  created_at timestamp with time zone not null default now(),
  total_items int not null,
  correct_count int not null default 0,
  wrong_count int not null default 0,
  status text not null default 'active' check (status in ('active', 'completed'))
);

create table if not exists study_plan_items (
  id uuid primary key default gen_random_uuid(),
  plan_id uuid not null references study_plans(id) on delete cascade,
  question_id uuid not null references questions(id) on delete cascade,
  position int not null,
  is_correct boolean,
  answered_at timestamp with time zone,
  unique (plan_id, position)
);

create table if not exists study_sessions (
  id uuid primary key default gen_random_uuid(),
  user_id uuid not null references users(id) on delete cascade,
  created_at timestamp with time zone not null default now(),
  total_cards int not null,
  correct_count int not null,
  wrong_count int not null
);

create table if not exists task_scans (
  id uuid primary key default gen_random_uuid(),
  user_id uuid not null references users(id) on delete cascade,
  question_id uuid references questions(id) on delete set null,
  image_url text not null,
  ocr_text text,
  ai_feedback text,
  is_correct boolean,
  created_at timestamp with time zone not null default now()
);
