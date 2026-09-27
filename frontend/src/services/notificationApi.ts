import { api } from "./api";
import type { Notification } from "../types/notification";

export interface NotificationTargetDetail {
  notification: Notification;
  user: { id:number; full_name:string; display_name:string; email:string|null; phone:string; date_of_birth:string|null; state_name:string|null; district_name:string|null; role:string };
  case: { id:number; case_number:string; category:string; status:string; stage:string; summary:string|null; protection_request_open:boolean; documents:Array<{id:number;filename:string;mime_type:string;status:string;uploaded_at:string;size_bytes:number|null;is_demo:boolean}> } | null;
}

export const notificationApi = {
  async list(): Promise<Notification[]> {
    const { data } = await api.get<Notification[]>("/notifications");
    return data;
  },

  async markRead(id: number): Promise<Notification> {
    const { data } = await api.post<Notification>(`/notifications/${id}/read`);
    return data;
  },

  async targetDetails(id: number): Promise<NotificationTargetDetail> { const { data } = await api.get<NotificationTargetDetail>(`/notifications/${id}/target-details`); return data; },

  async markAllRead(): Promise<{ updated_count: number }> {
    const { data } = await api.post<{ updated_count: number }>("/notifications/read-all");
    return data;
  },
};
