# SecondCommit
## Product and Development Plan

**Project Status:** Planning  
**Product Type:** Project Handoff and Revival Platform  
**Primary Integration:** GitHub  

> **Every project deserves a second commit.**

---

## 1. Product Vision

SecondCommit is a platform that helps developers preserve the knowledge behind unfinished software projects and transfer that context to developers interested in continuing them.

The platform is **not intended to replace GitHub**.

GitHub remains the source code hosting and development platform.

SecondCommit provides a structured layer for:

- Project handoff
- Revival discovery
- Developer context preservation
- Revival team formation
- Revival planning

The long-term goal is to reduce the amount of useful software work that becomes permanently inactive because project knowledge is lost.

---

## 2. Problem Definition

An inactive GitHub repository may contain valuable code.

However, repository inactivity alone does not explain the state of the project.

A developer discovering the repository may not know:

1. Why development stopped
2. Whether the owner wants the project continued
3. Which features are functional
4. Which features are incomplete
5. What technical blockers exist
6. Which solutions have already been attempted
7. What technical debt exists
8. What the original developer planned next
9. Which skills are required
10. Where development should continue

The developer can fork the repository.

The developer cannot automatically inherit the original developer's project knowledge.

This creates a **project context gap**.

SecondCommit is designed to reduce this gap.

---

## 3. Product Positioning

SecondCommit should **not** be positioned as:

> A marketplace for abandoned GitHub repositories.

This positioning is weak because public repositories can already be discovered and forked through GitHub.

SecondCommit should be positioned as:

> **A structured handoff and revival platform for unfinished software projects.**

The product value is not repository access.

The product value is **project context**.

---

## 4. Core Value Proposition

GitHub provides:

- Source code
- Commit history
- Issues
- Pull requests
- Repository collaboration

SecondCommit provides:

- Explicit owner revival intent
- Structured project handoff
- Original project vision
- Reason development stopped
- Working and incomplete feature context
- Known technical blockers
- Failed approach documentation
- Technical debt context
- Planned future direction
- Recommended revival starting point
- Revival team formation
- Revival progress

### Core Product Statement

> **A fork gives you the code. SecondCommit tells you how to continue it.**

---

## 5. Target Users

### 5.1 Project Owners

Developers who have an unfinished or inactive project and want:

- Contributors
- A co-maintainer
- A new maintainer
- Someone to continue the project

Examples:

- Students
- Indie developers
- Open-source developers
- Hackathon teams
- Early-stage project teams

### 5.2 Revival Developers

Developers who want:

- Real projects to contribute to
- Existing codebases to learn from
- Portfolio experience
- Open-source experience
- Team collaboration experience
- Projects matching their technical skills

---

## 6. Core Product Workflow

```text
GitHub Authentication
          ↓
Repository Selection
          ↓
Repository Import
          ↓
Revival Brief Creation
          ↓
Revival Intent Selection
          ↓
Project Publication
          ↓
Project Discovery
          ↓
Handoff Review
          ↓
Revival Request
          ↓
Owner Decision
          ↓
Revival Team Formation
          ↓
Project Revival
```

---

## 7. Core Feature: Revival Brief

The **Revival Brief** is the primary product differentiator.

It should be treated as a core domain entity rather than a generic project description.

### 7.1 Original Vision

**Question:**

> What were you originally trying to build?

**Purpose:**

Help new developers understand the intended outcome of the project.

---

### 7.2 Reason Development Stopped

**Question:**

> Why did you stop actively working on this project?

Possible predefined options:

- Lack of time
- Missing technical expertise
- Team became inactive
- Technical blocker
- Changed priorities
- Lost motivation
- Academic commitments
- Work commitments
- Other

An optional detailed explanation should also be available.

---

### 7.3 Working Features

**Question:**

> What currently works?

The owner should be able to add multiple items.

Example:

```text
Authentication
CSV export
REST API
User dashboard
```

---

### 7.4 Incomplete Features

**Question:**

> What still needs to be completed?

The owner should add individual incomplete items.

Example:

```text
PDF export
Deployment
Integration testing
```

---

### 7.5 Known Problems

**Question:**

> What known bugs or technical blockers should a new developer understand?

**Purpose:**

Prevent contributors from discovering major problems only after joining.

---

### 7.6 Failed Approaches

**Question:**

> What solutions have you already tried that did not work?

This is an important SecondCommit feature.

Example:

```text
Initially used Selenium for dynamic pages.

The deployment image became too large and browser management
was unreliable.

The project later moved to Playwright.
```

This information can save future developers significant time.

---

### 7.7 Technical Debt

**Question:**

> Which parts of the project need refactoring or architectural improvement?

Example:

```text
Parser logic is tightly coupled to export logic.

The modules should eventually be separated.
```

---

### 7.8 Planned Features

**Question:**

> What were you planning to build next?

**Purpose:**

Preserve the original development direction.

---

### 7.9 Required Skills

The owner selects or enters skills useful for project revival.

Examples:

```text
Python
FastAPI
PostgreSQL
React
Docker
```

---

### 7.10 Recommended Starting Point

**Question:**

> If someone joined the project today, what should they work on first?

This field should be strongly encouraged.

Example:

```text
Start by running the PDF export workflow.

The main issue is in table serialization between the parser
and PDF renderer.
```

---

## 8. Revival Intent

Each project must specify the owner's intent.

### Looking for Contributors

The owner remains responsible for the project and wants additional developers.

### Looking for Co-Maintainer

The owner wants another developer to share project responsibility.

### Looking for New Maintainer

The owner wants someone else to become the primary active maintainer.

### Available for Complete Handoff

The original developer intends to step away and wants another developer or team to continue the project.

> **Important:** SecondCommit revival intent does not automatically transfer GitHub repository ownership or permissions.

GitHub repository access remains controlled through GitHub.

---

## 9. Revival Status

Initial statuses:

```text
SEEKING_REVIVAL
FORMING_TEAM
REVIVAL_IN_PROGRESS
REVIVED
PAUSED
ARCHIVED
```

Suggested state flow:

```text
SEEKING_REVIVAL
       ↓
FORMING_TEAM
       ↓
REVIVAL_IN_PROGRESS
       ↓
REVIVED
```

Project owners manually control status during the MVP.

---

## 10. MVP Requirements

The MVP should prove one hypothesis:

> **Developers find structured project context valuable when deciding whether to continue an unfinished project.**

The MVP does not need AI.

The MVP does not need payments.

The MVP does not need complex repository analysis.

The MVP **must make the Revival Brief useful**.

---

## 11. MVP Feature Scope

### 11.1 Authentication

Requirements:

- GitHub OAuth login
- OAuth callback handling
- User creation
- User session
- Logout

Store:

- GitHub user ID
- Username
- Avatar URL
- Public profile URL

Email should only be stored if provided through the authorized GitHub OAuth/API flow and required by the application.

---

### 11.2 Repository Selection

Authenticated users should be able to view repositories available through the authorized GitHub API scope.

For the MVP:

- Display repository name
- Display description
- Display primary language
- Display repository visibility where relevant
- Allow repository selection

### Initial MVP Recommendation

Support **public repositories first**.

Private repository support introduces additional permission, privacy, and data-handling requirements and should be evaluated separately.

---

### 11.3 Project Creation

After repository selection, the owner creates a SecondCommit project.

Required fields:

- Repository
- Category
- Revival intent
- Original vision
- Reason stopped
- Recommended starting point

Additional Revival Brief fields should be available during project creation.

---

### 11.4 Project Publication

Projects can exist as:

```text
DRAFT
PUBLISHED
ARCHIVED
```

Draft projects are visible only to the owner.

Published projects appear in discovery.

Archived projects do not accept new revival requests.

---

### 11.5 Project Discovery

MVP discovery requirements:

- Browse published projects
- Search by project title
- Filter by primary language
- Filter by category
- Filter by revival intent

Do not build a complex recommendation engine during the MVP.

---

### 11.6 Project Detail Page

The project detail page should display:

#### Repository Summary

- Repository name
- Description
- Primary language
- Repository link
- Basic repository statistics

#### Revival State

- Revival intent
- Revival status

#### Revival Brief

- Original vision
- Reason development stopped
- Working features
- Incomplete features
- Known problems
- Failed approaches
- Technical debt
- Planned features
- Skills needed
- Recommended starting point

#### Revival Team

Display accepted revival team members.

#### Revival Action

Authenticated users can send a revival request.

---

### 11.7 Revival Requests

Request fields:

- Project
- Requesting user
- Introduction
- Relevant skills
- Contribution interest
- Request status

Statuses:

```text
PENDING
ACCEPTED
REJECTED
WITHDRAWN
```

Rules:

- Project owners cannot request to join their own project
- A user should not create multiple active requests for the same project
- Archived projects cannot accept requests
- Accepted users become revival team members

---

### 11.8 Dashboard

Dashboard sections:

#### My Projects

Projects owned by the current user.

#### Joined Revivals

Projects where the current user is an accepted revival team member.

#### Incoming Requests

Requests for projects owned by the user.

#### Sent Requests

Requests created by the user.

---

## 12. Initial Database Design

### User

```text
id
github_id
github_username
avatar_url
github_profile_url
created_at
updated_at
```

Constraints:

```text
github_id UNIQUE
github_username UNIQUE
```

---

### Project

```text
id
owner_id
github_repo_id
repository_name
repository_full_name
repository_url
repository_description
primary_language
category
revival_intent
revival_status
publication_status
created_at
updated_at
```

Relationships:

```text
Project.owner_id → User.id
```

---

### RevivalBrief

```text
id
project_id
original_vision
reason_stopped
reason_stopped_details
known_problems
failed_approaches
technical_debt
planned_features
recommended_starting_point
created_at
updated_at
```

Relationship:

```text
RevivalBrief.project_id → Project.id
```

`Project` and `RevivalBrief` have a one-to-one relationship.

---

### WorkingFeature

```text
id
revival_brief_id
title
position
```

---

### IncompleteFeature

```text
id
revival_brief_id
title
position
```

---

### ProjectSkill

```text
id
project_id
skill_name
```

---

### RevivalRequest

```text
id
project_id
requester_id
introduction
relevant_skills
contribution_interest
status
created_at
updated_at
```

Relationships:

```text
RevivalRequest.project_id → Project.id
RevivalRequest.requester_id → User.id
```

---

### RevivalTeamMember

```text
id
project_id
user_id
role
joined_at
```

Initial roles:

```text
CONTRIBUTOR
CO_MAINTAINER
REVIVAL_LEAD
```

---

## 13. Proposed Backend Architecture

```text
backend/
│
├── app/
│   ├── api/
│   │   ├── auth.py
│   │   ├── users.py
│   │   ├── repositories.py
│   │   ├── projects.py
│   │   └── revival_requests.py
│   │
│   ├── models/
│   │   ├── user.py
│   │   ├── project.py
│   │   ├── revival_brief.py
│   │   ├── revival_request.py
│   │   └── revival_team.py
│   │
│   ├── schemas/
│   │   ├── user.py
│   │   ├── project.py
│   │   ├── revival_brief.py
│   │   └── revival_request.py
│   │
│   ├── services/
│   │   ├── github_service.py
│   │   ├── project_service.py
│   │   └── revival_service.py
│   │
│   ├── core/
│   │   ├── config.py
│   │   ├── security.py
│   │   └── dependencies.py
│   │
│   ├── database/
│   │   ├── base.py
│   │   └── session.py
│   │
│   └── main.py
│
├── tests/
├── requirements.txt
└── .env.example
```

---

## 14. Proposed Frontend Architecture

```text
frontend/
│
├── app/
│   ├── page.tsx
│   ├── login/
│   ├── discover/
│   ├── projects/
│   │   ├── new/
│   │   └── [id]/
│   ├── dashboard/
│   └── profile/
│
├── components/
│   ├── projects/
│   ├── revival/
│   ├── dashboard/
│   └── ui/
│
├── lib/
│   ├── api.ts
│   ├── auth.ts
│   └── types.ts
│
├── public/
└── package.json
```

---

## 15. Development Milestones

### Milestone 1: Foundation

**Goal:** Create a working frontend, backend, and database foundation.

#### Tasks

- [ ] Initialize Next.js
- [ ] Initialize FastAPI
- [ ] Configure PostgreSQL
- [ ] Configure SQLAlchemy
- [ ] Configure environment variables
- [ ] Add backend health endpoint
- [ ] Connect frontend to backend
- [ ] Create `.env.example`
- [ ] Configure `.gitignore`

#### Expected Result

```text
Frontend running
Backend running
Database connected
Frontend can reach backend
```

---

### Milestone 2: GitHub Authentication

**Goal:** Allow users to authenticate through GitHub.

#### Tasks

- [ ] Create GitHub OAuth App
- [ ] Add login endpoint
- [ ] Redirect to GitHub authorization
- [ ] Handle OAuth callback
- [ ] Fetch GitHub user profile
- [ ] Create or update user
- [ ] Create authenticated session
- [ ] Add logout
- [ ] Add current-user endpoint

#### Expected Result

```text
User clicks Sign in with GitHub
        ↓
GitHub Authorization
        ↓
SecondCommit Callback
        ↓
User Created
        ↓
Authenticated Dashboard
```

---

### Milestone 3: Repository Import

**Goal:** Allow authenticated users to select a repository.

#### Tasks

- [ ] Create GitHub API service
- [ ] Fetch user repositories
- [ ] Display repositories
- [ ] Select repository
- [ ] Fetch repository metadata
- [ ] Validate repository
- [ ] Begin project creation

#### Expected Result

The user can select a GitHub repository to create a SecondCommit revival project.

---

### Milestone 4: Revival Brief

**Goal:** Build the primary SecondCommit feature.

#### Tasks

- [ ] Create Project model
- [ ] Create Revival Brief model
- [ ] Create Working Feature model
- [ ] Create Incomplete Feature model
- [ ] Create Project Skill model
- [ ] Build Revival Brief API
- [ ] Build Revival Brief form
- [ ] Add validation
- [ ] Support draft projects
- [ ] Publish completed handoff

#### Expected Result

A developer can create a complete structured project handoff.

> **This milestone is the most important milestone in the MVP.**

---

### Milestone 5: Discovery

**Goal:** Allow developers to discover projects seeking revival.

#### Tasks

- [ ] Create discovery API
- [ ] Display published projects
- [ ] Add project cards
- [ ] Add search
- [ ] Add language filter
- [ ] Add category filter
- [ ] Add revival intent filter
- [ ] Create project detail page

#### Expected Result

Developers can discover and understand projects before opening GitHub.

---

### Milestone 6: Revival Requests

**Goal:** Allow developers to express interest in reviving projects.

#### Tasks

- [ ] Create Revival Request model
- [ ] Send request
- [ ] View incoming requests
- [ ] View sent requests
- [ ] Accept request
- [ ] Reject request
- [ ] Withdraw pending request
- [ ] Create revival team membership

#### Expected Result

Project owners can form revival teams.

---

### Milestone 7: Dashboard and Project Management

**Goal:** Provide users with a central project management view.

#### Tasks

- [ ] My Projects
- [ ] Joined Revivals
- [ ] Incoming Requests
- [ ] Sent Requests
- [ ] Edit Revival Brief
- [ ] Update revival status
- [ ] Archive project

#### Expected Result

Users can manage their SecondCommit activity.

---

### Milestone 8: Manual Revival Roadmap

**Goal:** Help revival teams understand the project's next steps.

#### Tasks

- [ ] Create Roadmap model
- [ ] Create roadmap phases
- [ ] Create roadmap tasks
- [ ] Update task status
- [ ] Display revival progress

#### Expected Result

A revival project has a structured continuation plan.

---

### Milestone 9: Repository Health Signals

**Goal:** Add useful GitHub context without attempting full code analysis.

#### Tasks

- [ ] Fetch last repository update
- [ ] Fetch open issue count
- [ ] Fetch basic repository activity
- [ ] Cache GitHub metadata
- [ ] Define health signals
- [ ] Display contextual indicators

#### Expected Result

Developers receive additional repository context.

> Avoid misleading numerical scores until the scoring logic is validated.

---

### Milestone 10: AI Handoff Assistant

**Goal:** Reduce the effort required to create a Revival Brief.

#### Tasks

- [ ] Define repository analysis boundaries
- [ ] Extract safe repository context
- [ ] Analyze project structure
- [ ] Generate draft observations
- [ ] Suggest possible incomplete areas
- [ ] Suggest initial revival tasks
- [ ] Require owner review
- [ ] Allow owner editing

#### Expected Result

AI assists the original developer in preparing a handoff.

AI does not automatically publish project claims.

---

### Milestone 11: Testing and Deployment

**Goal:** Prepare SecondCommit for an initial public release.

#### Tasks

- [ ] Add backend tests
- [ ] Test OAuth workflow
- [ ] Test project handoff workflow
- [ ] Test revival request workflow
- [ ] Deploy frontend
- [ ] Deploy backend
- [ ] Configure production database
- [ ] Configure production GitHub OAuth

---

## 16. MVP Non-Goals

Do **not** implement these during the initial MVP:

- Payments
- Project selling
- Repository ownership transfer
- Real-time chat
- Video calls
- Social media feed
- Follower system
- Complex notifications
- AI contributor matching
- Automatic pull request review
- Full source code quality analysis
- GitHub issue synchronization
- Mobile application

These features increase development complexity without validating the core product idea.

---

## 17. GitHub API Usage Strategy

GitHub API requests should not be performed unnecessarily on every page load.

Recommended flow:

```text
GitHub API
     ↓
Fetch Repository Metadata
     ↓
Store Required Cached Metadata
     ↓
SecondCommit Database
     ↓
Frontend
```

Repository metadata should be refreshed using an appropriate caching strategy.

Do not treat cached GitHub metadata as permanently current.

---

## 18. Security Considerations

### OAuth Secrets

Never expose:

```text
GITHUB_CLIENT_SECRET
DATABASE_URL
SESSION_SECRET
```

Secrets must remain in backend environment variables.

### OAuth Access Tokens

GitHub access tokens must never be returned to the frontend.

If tokens are persisted, they must be protected appropriately and access should be limited to required backend operations.

The token storage strategy should be reviewed before production deployment.

### Repository Permissions

Request the minimum GitHub permissions required by the application.

Public repository support should be prioritized during the MVP.

Do not request broad repository permissions without a clear product requirement.

### Project Ownership

Only the SecondCommit project owner should be allowed to:

- Edit the Revival Brief
- Change revival intent
- Change project status
- Archive the project
- Review revival requests

---

## 19. Product Validation

Before building advanced AI features, test whether users find the Revival Brief valuable.

Questions to validate:

1. Would developers list unfinished projects?
2. Are project owners willing to document why development stopped?
3. Do developers read the Revival Brief before opening the repository?
4. Does the Revival Brief reduce project understanding time?
5. Do developers send revival requests?
6. Do project owners accept revival developers?
7. Do accepted developers make actual contributions?

The most important success signal is **not user registrations**.

The most important success signal is:

> **A previously inactive project receives meaningful development activity after a SecondCommit handoff.**

---

## 20. Initial Success Metrics

MVP targets:

```text
25 Published Revival Projects
100 Registered Developers
30 Revival Requests
10 Revival Teams Formed
5 Projects Return to Active Development
```

These are product validation targets, not guaranteed outcomes.

---

## 21. Future Product Directions

Possible future expansions include:

### AI Project Handoff

Generate editable draft handoff information from repository context.

### Contributor Matching

Match developer skills with revival project requirements.

### GitHub Issue Integration

Convert Revival Roadmap tasks into GitHub issues.

### Revival Activity Tracking

Track repository activity after revival begins.

### Project Revival Stories

Document successful project revival journeys.

### Organization Handoffs

Allow teams and small organizations to hand off internal or open-source projects.

These features should only be prioritized after validating the core handoff workflow.

---

## 22. Core Product Principle

SecondCommit should always answer one question:

> **What information does a developer need to continue a project they did not originally build?**

Every major feature should support that question.

If a proposed feature does not improve:

- Project understanding
- Knowledge transfer
- Revival discovery
- Team formation
- Project continuation

it should not be prioritized during the MVP.

---

## Final Product Definition

SecondCommit is a **structured project handoff and revival platform built around GitHub repositories**.

It helps original developers preserve the knowledge behind unfinished projects and helps new developers understand how to continue them.

> **GitHub preserves the code. SecondCommit preserves the context needed to continue it.**

<p align="center">
  <strong>Every project deserves a second commit.</strong>
</p>