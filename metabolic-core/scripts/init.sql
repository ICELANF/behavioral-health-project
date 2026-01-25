-- Enable UUID extension
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Create enum types
CREATE TYPE certification_level AS ENUM ('L0', 'L1', 'L2', 'L3', 'L4');
CREATE TYPE exam_type AS ENUM ('theory', 'case_simulation', 'dialogue_assessment', 'specialty');
CREATE TYPE module_type AS ENUM ('knowledge', 'method', 'skill', 'value');
CREATE TYPE question_type AS ENUM ('single', 'multiple', 'truefalse', 'short_answer');
CREATE TYPE risk_level AS ENUM ('low', 'medium', 'high');
CREATE TYPE coach_status AS ENUM ('active', 'inactive', 'suspended', 'pending_review');
CREATE TYPE case_status AS ENUM ('ongoing', 'completed', 'abandoned');
CREATE TYPE platform_rating AS ENUM ('S', 'A+', 'A', 'A-', 'B+', 'B', 'B-', 'C', 'D');
CREATE TYPE permission_level AS ENUM ('read', 'execute', 'configure');
CREATE TYPE exam_status AS ENUM ('draft', 'published', 'archived');
CREATE TYPE result_status AS ENUM ('passed', 'failed');
CREATE TYPE application_status AS ENUM ('pending', 'under_review', 'approved', 'rejected', 'need_supplement');
CREATE TYPE mentoring_outcome AS ENUM ('promoted', 'ongoing', 'dropped');

-- Grant all privileges to the user
GRANT ALL PRIVILEGES ON DATABASE behavioral_health TO bhp_user;
