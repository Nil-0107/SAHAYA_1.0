import { api } from "./api";
import type { ProfileResponse, ProfileSetupPayload } from "../types/profile";

export const profileApi = {
  async setup(payload: ProfileSetupPayload): Promise<ProfileResponse> {
    const { data } = await api.post<ProfileResponse>("/profile", payload);
    return data;
  },

  async get(): Promise<ProfileResponse> {
    const { data } = await api.get<ProfileResponse>("/profile");
    return data;
  },
};
