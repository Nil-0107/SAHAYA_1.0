import { api } from "./api";
import type { AdminDashboard, AdminUserDetail } from "../types/admin";
import type { AdministrativeAccount, AdministrativeUnit } from "../types/administration";

export const adminApi = {
  async users(includeDemo = false): Promise<AdminUserDetail[]> { const { data } = await api.get<AdminUserDetail[]>("/admin/users", { params: { include_demo: includeDemo } }); return data; },

  async dashboard(includeDemo = false): Promise<AdminDashboard> {
    const { data } = await api.get<AdminDashboard>("/admin/dashboard", { params: { include_demo: includeDemo } });
    return data;
  },

  async listStateAdministrators(): Promise<AdministrativeAccount[]> {
    const { data } = await api.get<AdministrativeAccount[]>("/admin/state-administrators");
    return data;
  },

  async createStateAdministrator(payload: Record<string, unknown>): Promise<AdministrativeAccount> {
    const { data } = await api.post<AdministrativeAccount>("/admin/state-administrators", payload);
    return data;
  },

  async listDistrictAdministrators(): Promise<AdministrativeAccount[]> {
    const { data } = await api.get<AdministrativeAccount[]>("/admin/district-administrators");
    return data;
  },

  async createDistrictAdministrator(payload: Record<string, unknown>): Promise<AdministrativeAccount> {
    const { data } = await api.post<AdministrativeAccount>("/admin/district-administrators", payload);
    return data;
  },

  async listCounsellors(): Promise<AdministrativeAccount[]> {
    const { data } = await api.get<AdministrativeAccount[]>("/admin/counsellors");
    return data;
  },

  async createCounsellor(payload: Record<string, unknown>): Promise<AdministrativeAccount> {
    const { data } = await api.post<AdministrativeAccount>("/admin/counsellors", payload);
    return data;
  },

  async listStates(): Promise<AdministrativeUnit[]> {
    const { data } = await api.get<AdministrativeUnit[]>("/admin/states");
    return data;
  },

  async listDistricts(): Promise<AdministrativeUnit[]> {
    const { data } = await api.get<AdministrativeUnit[]>("/admin/districts");
    return data;
  },

  async setAccountStatus(userId: number, status: "active" | "suspended"): Promise<AdministrativeAccount> {
    const { data } = await api.patch<AdministrativeAccount>(`/admin/accounts/${userId}/status`, { status });
    return data;
  },

  async createAssignment(payload: { support_request_id: number; assignee_user_id: number; assignment_type: "wellbeing_counsellor"; reason: string }): Promise<void> {
    await api.post("/case-assignments", payload);
  },
};
