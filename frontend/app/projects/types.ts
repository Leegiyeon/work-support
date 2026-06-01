export type ProjectStatus = "idea" | "review" | "in_progress" | "on_hold" | "done";
export type TaskStatus = "planned" | "in_progress" | "done" | "on_hold";
export type TaskPriority = "low" | "medium" | "high";

export type ProjectSummary = {
  id: string;
  title: string;
  description: string;
  status: ProjectStatus;
  role: string;
  total_tasks: number;
  completed_tasks: number;
  remaining_tasks: number;
  progress_percent: number;
  updated_at: string;
};

export type ProjectTask = {
  id: string;
  project_id: string;
  title: string;
  description: string;
  status: TaskStatus;
  priority: TaskPriority;
  due_date: string | null;
  created_at: string;
  updated_at: string;
};

export const projectStatusLabels: Record<ProjectStatus, string> = {
  idea: "아이디어",
  review: "검토",
  in_progress: "진행",
  on_hold: "보류",
  done: "완료"
};

export const taskStatusLabels: Record<TaskStatus, string> = {
  planned: "예정",
  in_progress: "진행",
  done: "완료",
  on_hold: "보류"
};

export const taskPriorityLabels: Record<TaskPriority, string> = {
  low: "낮음",
  medium: "보통",
  high: "높음"
};
