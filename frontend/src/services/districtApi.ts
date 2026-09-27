import { api } from "./api";
import type { DistrictDashboard } from "../types/district";

export const districtApi = {
  async dashboard(): Promise<DistrictDashboard> {
    const { data } = await api.get<DistrictDashboard>("/district/dashboard");
    return data;
  },
};
