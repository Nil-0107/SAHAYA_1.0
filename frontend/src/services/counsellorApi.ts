import { api } from "./api";
import type { CounsellorDashboard, CounsellorUserDetail } from "../types/counsellor";

export const counsellorApi = {
  async users(): Promise<CounsellorUserDetail[]> { const { data } = await api.get<CounsellorUserDetail[]>("/counsellor/users"); return data; },
  async dashboard(): Promise<CounsellorDashboard> {
    const { data } = await api.get<CounsellorDashboard>("/counsellor/dashboard");
    return data;
  },
};
