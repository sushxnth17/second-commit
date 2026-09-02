const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

export interface UserSummary {
  id?: number;
  github_id: number;
  username: string;
  name: string | null;
  avatar_url?: string | null;
}

export interface RepositorySummary {
  id: number;
  name: string;
  language: string | null;
  default_branch: string;
  stars?: number | null;
  forks?: number | null;
  open_issues?: number | null;
  size?: number | null;
  description?: string | null;
  pushed_at?: string | null;
  health_score?: number;
  health_grade?: string;
  dormancy_status?: string;
  published?: boolean;
}

export interface OwnerSummary {
  username: string;
  name: string | null;
  avatar_url: string | null;
}

export interface RevivalBriefResponse {
  id: number;
  repository_id: number;
  developer_notes: string;
  revival_intent: string;
  status: string;
  created_at: string;
  updated_at: string;
}

export interface RevivalBriefPayload {
  developer_notes?: string;
  revival_intent?: string;
  status?: string;
}

export interface RequesterSummary {
  username: string;
  name: string | null;
  avatar_url: string | null;
}

export interface RevivalRequestResponse {
  id: number;
  repository_id: number;
  requester_id: number;
  message: string | null;
  status: string;
  created_at: string;
  updated_at: string;
  requester?: RequesterSummary | null;
}

export interface TeamUserSummary {
  id: number;
  username: string;
  name: string | null;
  avatar_url: string | null;
}

export interface RevivalTeamMemberResponse {
  id: number;
  team_id: number;
  user_id: number;
  joined_at: string;
  user?: TeamUserSummary | null;
  username?: string | null;
  name?: string | null;
  avatar_url?: string | null;
}

export interface RevivalTeamResponse {
  id: number;
  repository_id: number;
  owner_id: number;
  created_at: string;
  updated_at: string;
  owner?: TeamUserSummary | null;
  members: RevivalTeamMemberResponse[];
}


export interface RepositoryResponse {
  id: number;
  github_repo_id: number;
  name: string;
  full_name: string;
  description: string | null;
  html_url: string;
  language: string | null;
  default_branch: string;
  stars: number | null;
  forks: number | null;
  watchers: number | null;
  open_issues: number | null;
  size: number | null;
  created_at: string | null;
  updated_at: string | null;
  pushed_at: string | null;
  published: boolean;
  owner?: OwnerSummary | null;
}

export interface DashboardResponse {
  user: UserSummary;
  repositories: RepositorySummary[];
  total_repositories: number;
}

export interface HealthResponse {
  repository_id: number;
  repository_name: string;
  health_score: number;
  grade: string;
  summary: string;
}

export interface DormancyResponse {
  repository_id: number;
  repository_name: string;
  days_since_last_push: number;
  status: string;
  message: string;
}

export interface AnalyticsResponse {
  github_id: number;
  username: string;
  total_repositories: number;
  total_stars: number;
  total_forks: number;
  active_repositories: number;
  dormant_repositories: number;
  primary_language: string | null;
  most_popular_repository: string | null;
  most_active_repository: string | null;
  average_health_score: number | null;
}

export interface AIInsightsResponse {
  repository_id: number;
  repository_name: string;
  summary: string;
  strengths: string[];
  weaknesses: string[];
  suggestions: string[];
  beginner_friendly: boolean;
  complexity: string;
  ai_score: number;
}

export interface GitHubRepo {
  id: number;
  name: string;
  full_name: string;
  description: string | null;
  html_url: string;
  language: string | null;
  default_branch: string;
}

async function request<T>(path: string, options?: RequestInit): Promise<T> {
  const url = `${API_URL}${path}`;
  const response = await fetch(url, {
    ...options,
    headers: {
      "Content-Type": "application/json",
      ...(options?.headers || {}),
    },
    credentials: "include", // Ensure session cookies are sent/received
  });

  if (!response.ok) {
    if (response.status === 401) {
      throw new Error("UNAUTHORIZED");
    }
    const errText = await response.text();
    let detail = "An error occurred";
    try {
      const parsed = JSON.parse(errText);
      detail = parsed.detail || detail;
    } catch {}
    throw new Error(detail);
  }

  if (response.status === 204) {
    return undefined as T;
  }

  return response.json();
}

export const api = {
  // Authentication url helper
  getLoginUrl() {
    return `${API_URL}/auth/github`;
  },

  // Logout helper
  logout(): Promise<{ message: string }> {
    return request<{ message: string }>("/auth/logout", {
      method: "POST",
    });
  },

  // Dashboard endpoint
  getDashboard(): Promise<DashboardResponse> {
    return request<DashboardResponse>("/dashboard");
  },

  // Developer analytics
  getAnalytics(): Promise<AnalyticsResponse> {
    return request<AnalyticsResponse>("/analytics");
  },

  // GitHub repositories (available to import)
  getGitHubRepositories(): Promise<GitHubRepo[]> {
    return request<GitHubRepo[]>("/github/repositories");
  },

  // Import repository
  importRepository(repoId: number): Promise<{ message: string; repository: { id: number; name: string } }> {
    return request(`/repositories/import/${repoId}`, {
      method: "POST",
    });
  },

  // Get specific repository
  getRepository(id: number): Promise<RepositoryResponse> {
    return request<RepositoryResponse>(`/repositories/${id}`);
  },

  // Sync repository
  syncRepository(id: number): Promise<RepositoryResponse> {
    return request<RepositoryResponse>(`/repositories/${id}/sync`, {
      method: "POST",
    });
  },

  // Repository Health
  getRepositoryHealth(id: number): Promise<HealthResponse> {
    return request<HealthResponse>(`/repositories/${id}/health`);
  },

  // Repository Dormancy
  getRepositoryDormancy(id: number): Promise<DormancyResponse> {
    return request<DormancyResponse>(`/repositories/${id}/dormancy`);
  },

  // AI Insights
  getRepositoryAIInsights(id: number): Promise<AIInsightsResponse> {
    return request<AIInsightsResponse>(`/repositories/${id}/ai-insights`);
  },

  // Publish repository
  publishRepository(id: number): Promise<RepositoryResponse> {
    return request<RepositoryResponse>(`/repositories/${id}/publish`, {
      method: "POST",
    });
  },

  // Unpublish repository
  unpublishRepository(id: number): Promise<RepositoryResponse> {
    return request<RepositoryResponse>(`/repositories/${id}/unpublish`, {
      method: "POST",
    });
  },

  // Discover repositories
  discoverRepositories(): Promise<RepositoryResponse[]> {
    return request<RepositoryResponse[]>("/repositories/discover");
  },

  // Get Revival Brief
  getHandover(repositoryId: number): Promise<RevivalBriefResponse | null> {
    return request<RevivalBriefResponse | null>(`/repositories/${repositoryId}/handover`);
  },

  // Save Revival Brief
  saveHandover(repositoryId: number, payload: RevivalBriefPayload): Promise<RevivalBriefResponse> {
    return request<RevivalBriefResponse>(`/repositories/${repositoryId}/handover`, {
      method: "PUT",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify(payload),
    });
  },

  // Delete/Reset Revival Brief
  deleteHandover(repositoryId: number): Promise<{ status: string }> {
    return request<{ status: string }>(`/repositories/${repositoryId}/handover`, {
      method: "DELETE",
    });
  },

  // Create Revival Request
  createRevivalRequest(repositoryId: number, message?: string): Promise<RevivalRequestResponse> {
    return request<RevivalRequestResponse>(`/repositories/${repositoryId}/revival-requests`, {
      method: "POST",
      body: JSON.stringify({ message }),
    });
  },

  // Get My Pending Revival Request
  getMyPendingRevivalRequest(repositoryId: number): Promise<RevivalRequestResponse | null> {
    return request<RevivalRequestResponse | null>(`/repositories/${repositoryId}/revival-requests/my-pending`);
  },

  // Get My Latest Revival Request regardless of status
  getMyRevivalRequest(repositoryId: number): Promise<RevivalRequestResponse | null> {
    return request<RevivalRequestResponse | null>(`/repositories/${repositoryId}/revival-requests/my`);
  },

  // Get all Revival Requests (Owner-only)
  getRevivalRequests(repositoryId: number): Promise<RevivalRequestResponse[]> {
    return request<RevivalRequestResponse[]>(`/repositories/${repositoryId}/revival-requests`);
  },

  // Approve a Revival Request (Owner-only)
  approveRevivalRequest(repositoryId: number, requestId: number): Promise<RevivalRequestResponse> {
    return request<RevivalRequestResponse>(`/repositories/${repositoryId}/revival-requests/${requestId}/approve`, {
      method: "POST",
    });
  },

  // Reject a Revival Request (Owner-only)
  rejectRevivalRequest(repositoryId: number, requestId: number): Promise<RevivalRequestResponse> {
    return request<RevivalRequestResponse>(`/repositories/${repositoryId}/revival-requests/${requestId}/reject`, {
      method: "POST",
    });
  },

  // Get Revival Team
  async getRevivalTeam(repositoryId: number): Promise<RevivalTeamResponse | null> {
    try {
      return await request<RevivalTeamResponse>(`/repositories/${repositoryId}/revival-team`);
    } catch (err: any) {
      if (err.message === "Revival team not found" || err.message === "Repository not found") {
        return null;
      }
      throw err;
    }
  },

  // Remove Revival Team Member (Owner-only)
  removeRevivalTeamMember(repositoryId: number, userId: number): Promise<void> {
    return request<void>(`/repositories/${repositoryId}/revival-team/members/${userId}`, {
      method: "DELETE",
    });
  },

  // Leave Revival Team (Member-only)
  leaveRevivalTeam(repositoryId: number): Promise<void> {
    return request<void>(`/repositories/${repositoryId}/revival-team/members/me`, {
      method: "DELETE",
    });
  },
};
