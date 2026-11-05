export type TodoPriority = 'low' | 'medium' | 'high';
export type TodoStatus = 'all' | 'active' | 'completed';

export interface Todo {
  id: number;
  title: string;
  description?: string;
  completed: boolean;
  priority: TodoPriority;
  dueDate?: string;
  createdAt: string;
  updatedAt: string;
  userId?: number;
}

export interface TodoFilter {
  status: TodoStatus;
  priority?: TodoPriority;
  search?: string;
  sortBy: 'createdAt' | 'dueDate' | 'priority';
  sortOrder: 'asc' | 'desc';
}

export interface CreateTodoInput {
  title: string;
  description?: string;
  priority?: TodoPriority;
  dueDate?: string;
}

export interface UpdateTodoInput {
  title?: string;
  description?: string;
  priority?: TodoPriority;
  dueDate?: string;
  completed?: boolean;
}

export interface TodoStats {
  total: number;
  active: number;
  completed: number;
  highPriority: number;
  overdue: number;
}
