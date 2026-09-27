export interface Notification {
  id: number;
  case_id: number | null;
  type: string;
  title: string;
  message: string;
  is_read: boolean;
  read_at: string | null;
  created_at: string;
  is_demo: boolean;
}
