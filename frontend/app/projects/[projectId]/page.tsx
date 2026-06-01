"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { FormEvent, use, useEffect, useMemo, useState } from "react";

import { parseApiErrorMessage } from "../../reports/api-error";
import type { ProjectStatus, ProjectSummary, ProjectTask, TaskPriority, TaskStatus } from "../types";
import { projectStatusLabels, taskPriorityLabels, taskStatusLabels } from "../types";

type PageProps = {
  params: Promise<{ projectId: string }>;
};

type TaskForm = {
  title: string;
  description: string;
  status: TaskStatus;
  priority: TaskPriority;
  due_date: string;
};

type ProjectForm = {
  title: string;
  description: string;
  role: string;
  status: ProjectStatus;
};

const initialTaskForm: TaskForm = {
  title: "",
  description: "",
  status: "planned",
  priority: "medium",
  due_date: ""
};

const initialProjectForm: ProjectForm = {
  title: "",
  description: "",
  role: "",
  status: "idea"
};

export default function ProjectDetailPage({ params }: PageProps) {
  const { projectId } = use(params);
  const router = useRouter();
  const [project, setProject] = useState<ProjectSummary | null>(null);
  const [tasks, setTasks] = useState<ProjectTask[]>([]);
  const [projectForm, setProjectForm] = useState<ProjectForm>(initialProjectForm);
  const [taskForm, setTaskForm] = useState<TaskForm>(initialTaskForm);
  const [editingTaskId, setEditingTaskId] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [isSavingProject, setIsSavingProject] = useState(false);
  const [isSavingTask, setIsSavingTask] = useState(false);
  const [errorMessage, setErrorMessage] = useState("");

  const groupedTasks = useMemo(() => {
    return (Object.keys(taskStatusLabels) as TaskStatus[]).map((status) => ({
      status,
      label: taskStatusLabels[status],
      items: tasks.filter((task) => task.status === status)
    }));
  }, [tasks]);

  async function loadProject() {
    setIsLoading(true);
    setErrorMessage("");
    try {
      const [projectResponse, tasksResponse] = await Promise.all([
        fetch(`/api/projects/${projectId}`, { cache: "no-store" }),
        fetch(`/api/projects/${projectId}/tasks`, { cache: "no-store" })
      ]);
      if (!projectResponse.ok) {
        const detail = await projectResponse.json().catch(() => null);
        throw new Error(parseApiErrorMessage(detail));
      }
      if (!tasksResponse.ok) {
        const detail = await tasksResponse.json().catch(() => null);
        throw new Error(parseApiErrorMessage(detail));
      }
      const nextProject = (await projectResponse.json()) as ProjectSummary;
      setProject(nextProject);
      setProjectForm({
        title: nextProject.title,
        description: nextProject.description,
        role: nextProject.role,
        status: nextProject.status
      });
      setTasks((await tasksResponse.json()) as ProjectTask[]);
    } catch (error) {
      setErrorMessage(error instanceof Error ? error.message : "프로젝트 상세를 불러오지 못했습니다.");
    } finally {
      setIsLoading(false);
    }
  }

  useEffect(() => {
    let isMounted = true;

    Promise.all([
      fetch(`/api/projects/${projectId}`, { cache: "no-store" }),
      fetch(`/api/projects/${projectId}/tasks`, { cache: "no-store" })
    ])
      .then(async ([projectResponse, tasksResponse]) => {
        if (!projectResponse.ok) {
          const detail = await projectResponse.json().catch(() => null);
          throw new Error(parseApiErrorMessage(detail));
        }
        if (!tasksResponse.ok) {
          const detail = await tasksResponse.json().catch(() => null);
          throw new Error(parseApiErrorMessage(detail));
        }
        return Promise.all([projectResponse.json() as Promise<ProjectSummary>, tasksResponse.json() as Promise<ProjectTask[]>]);
      })
      .then(([nextProject, nextTasks]) => {
        if (isMounted) {
          setProject(nextProject);
          setProjectForm({
            title: nextProject.title,
            description: nextProject.description,
            role: nextProject.role,
            status: nextProject.status
          });
          setTasks(nextTasks);
        }
      })
      .catch((error: unknown) => {
        if (isMounted) {
          setErrorMessage(error instanceof Error ? error.message : "프로젝트 상세를 불러오지 못했습니다.");
        }
      })
      .finally(() => {
        if (isMounted) {
          setIsLoading(false);
        }
      });

    return () => {
      isMounted = false;
    };
  }, [projectId]);

  async function handleSaveProject(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!projectForm.title.trim()) {
      setErrorMessage("프로젝트명을 입력하세요.");
      return;
    }

    setIsSavingProject(true);
    setErrorMessage("");
    try {
      const response = await fetch(`/api/projects/${projectId}`, {
        method: "PATCH",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(projectForm)
      });
      if (!response.ok) {
        const detail = await response.json().catch(() => null);
        throw new Error(parseApiErrorMessage(detail));
      }
      await loadProject();
    } catch (error) {
      setErrorMessage(error instanceof Error ? error.message : "프로젝트를 저장하지 못했습니다.");
    } finally {
      setIsSavingProject(false);
    }
  }

  async function handleDeleteProject() {
    setErrorMessage("");
    const response = await fetch(`/api/projects/${projectId}`, { method: "DELETE" });
    if (!response.ok) {
      const detail = await response.json().catch(() => null);
      setErrorMessage(parseApiErrorMessage(detail));
      return;
    }
    router.push("/projects");
  }

  async function handleSaveTask(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!taskForm.title.trim()) {
      setErrorMessage("업무명을 입력하세요.");
      return;
    }

    const payload = {
      ...taskForm,
      due_date: taskForm.due_date || null
    };

    setIsSavingTask(true);
    setErrorMessage("");
    try {
      const response = await fetch(
        editingTaskId ? `/api/projects/${projectId}/tasks/${editingTaskId}` : `/api/projects/${projectId}/tasks`,
        {
          method: editingTaskId ? "PATCH" : "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify(payload)
        }
      );
      if (!response.ok) {
        const detail = await response.json().catch(() => null);
        throw new Error(parseApiErrorMessage(detail));
      }
      setTaskForm(initialTaskForm);
      setEditingTaskId(null);
      await loadProject();
    } catch (error) {
      setErrorMessage(error instanceof Error ? error.message : "업무를 저장하지 못했습니다.");
    } finally {
      setIsSavingTask(false);
    }
  }

  function startEdit(task: ProjectTask) {
    setEditingTaskId(task.id);
    setTaskForm({
      title: task.title,
      description: task.description,
      status: task.status,
      priority: task.priority,
      due_date: task.due_date ?? ""
    });
  }

  async function updateStatus(task: ProjectTask, status: TaskStatus) {
    setErrorMessage("");
    const response = await fetch(`/api/projects/${projectId}/tasks/${task.id}`, {
      method: "PATCH",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ status })
    });
    if (!response.ok) {
      const detail = await response.json().catch(() => null);
      setErrorMessage(parseApiErrorMessage(detail));
      return;
    }
    await loadProject();
  }

  async function deleteTask(task: ProjectTask) {
    setErrorMessage("");
    const response = await fetch(`/api/projects/${projectId}/tasks/${task.id}`, { method: "DELETE" });
    if (!response.ok) {
      const detail = await response.json().catch(() => null);
      setErrorMessage(parseApiErrorMessage(detail));
      return;
    }
    await loadProject();
  }

  return (
    <main className="page-shell project-page">
      <Link className="text-link" href="/projects">← 프로젝트 목록</Link>

      {isLoading ? <section className="panel muted">프로젝트를 불러오는 중입니다.</section> : null}
      {errorMessage ? <div className="alert error">{errorMessage}</div> : null}

      {project ? (
        <>
          <section className="hero-card compact">
            <p className="eyebrow">{projectStatusLabels[project.status]}</p>
            <h1>{project.title}</h1>
            <p className="hero-description">{project.description || "설명 없음"}</p>
            <div className="summary-grid inline">
              <div className="metric-card"><span>진척도</span><strong>{project.progress_percent}%</strong></div>
              <div className="metric-card"><span>잔여 업무</span><strong>{project.remaining_tasks}</strong></div>
              <div className="metric-card"><span>완료/전체</span><strong>{project.completed_tasks}/{project.total_tasks}</strong></div>
            </div>
          </section>

          <section className="panel">
            <h2>프로젝트 정보 수정</h2>
            <form className="stacked-form" onSubmit={handleSaveProject}>
              <div className="form-grid two-columns">
                <label>
                  프로젝트명
                  <input value={projectForm.title} onChange={(event) => setProjectForm({ ...projectForm, title: event.target.value })} />
                </label>
                <label>
                  상태
                  <select value={projectForm.status} onChange={(event) => setProjectForm({ ...projectForm, status: event.target.value as ProjectStatus })}>
                    {Object.entries(projectStatusLabels).map(([value, label]) => <option key={value} value={value}>{label}</option>)}
                  </select>
                </label>
              </div>
              <label>
                설명
                <textarea value={projectForm.description} onChange={(event) => setProjectForm({ ...projectForm, description: event.target.value })} placeholder="프로젝트 목적과 범위" />
              </label>
              <label>
                내 역할
                <input value={projectForm.role} onChange={(event) => setProjectForm({ ...projectForm, role: event.target.value })} placeholder="예: PM, 기획, 자동화 담당" />
              </label>
              <div className="form-actions">
                <button type="submit" disabled={isSavingProject}>{isSavingProject ? "저장 중..." : "프로젝트 저장"}</button>
                <button className="danger-button" type="button" onClick={() => void handleDeleteProject()}>프로젝트 삭제</button>
              </div>
            </form>
          </section>

          <section className="panel">
            <h2>{editingTaskId ? "업무 수정" : "업무 추가"}</h2>
            <form className="stacked-form" onSubmit={handleSaveTask}>
              <label>
                업무명
                <input value={taskForm.title} onChange={(event) => setTaskForm({ ...taskForm, title: event.target.value })} placeholder="예: 요구사항 정리" />
              </label>
              <label>
                설명
                <textarea value={taskForm.description} onChange={(event) => setTaskForm({ ...taskForm, description: event.target.value })} placeholder="업무 내용, 완료 기준, 참고 사항" />
              </label>
              <div className="form-grid three-columns">
                <label>
                  상태
                  <select value={taskForm.status} onChange={(event) => setTaskForm({ ...taskForm, status: event.target.value as TaskStatus })}>
                    {Object.entries(taskStatusLabels).map(([value, label]) => <option key={value} value={value}>{label}</option>)}
                  </select>
                </label>
                <label>
                  우선순위
                  <select value={taskForm.priority} onChange={(event) => setTaskForm({ ...taskForm, priority: event.target.value as TaskPriority })}>
                    {Object.entries(taskPriorityLabels).map(([value, label]) => <option key={value} value={value}>{label}</option>)}
                  </select>
                </label>
                <label>
                  마감일
                  <input type="date" value={taskForm.due_date} onChange={(event) => setTaskForm({ ...taskForm, due_date: event.target.value })} />
                </label>
              </div>
              <div className="form-actions">
                <button type="submit" disabled={isSavingTask}>{isSavingTask ? "저장 중..." : editingTaskId ? "수정 저장" : "업무 추가"}</button>
                {editingTaskId ? <button className="secondary-button" type="button" onClick={() => { setEditingTaskId(null); setTaskForm(initialTaskForm); }}>취소</button> : null}
              </div>
            </form>
          </section>

          <section className="task-board" aria-label="프로젝트별 업무 목록">
            {groupedTasks.map((group) => (
              <div className="panel task-column" key={group.status}>
                <h2>{group.label} <span className="count-badge">{group.items.length}</span></h2>
                {group.items.length === 0 ? <p className="muted-text">해당 상태의 업무가 없습니다.</p> : null}
                {group.items.map((task) => (
                  <article className="task-card" key={task.id}>
                    <h3>{task.title}</h3>
                    <p>{task.description || "설명 없음"}</p>
                    <div className="task-meta">
                      <span className={`meta-pill priority-${task.priority}`}>우선순위 {taskPriorityLabels[task.priority]}</span>
                      <span className="meta-pill">마감 {task.due_date ?? "없음"}</span>
                    </div>
                    <select value={task.status} onChange={(event) => void updateStatus(task, event.target.value as TaskStatus)} aria-label={`${task.title} 상태 변경`}>
                      {Object.entries(taskStatusLabels).map(([value, label]) => <option key={value} value={value}>{label}</option>)}
                    </select>
                    <div className="form-actions compact-actions">
                      <button className="secondary-button" type="button" onClick={() => startEdit(task)}>수정</button>
                      <button className="danger-button" type="button" onClick={() => void deleteTask(task)}>삭제</button>
                    </div>
                  </article>
                ))}
              </div>
            ))}
          </section>
        </>
      ) : null}
    </main>
  );
}
