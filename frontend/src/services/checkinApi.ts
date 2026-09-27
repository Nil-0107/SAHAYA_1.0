import { api } from "./api";
import type { Checkin } from "../types/checkin";

export interface CreateCheckinPayload {
  text: string;
  case_id?: number | null;
}

export const checkinApi = {
  async create(payload: CreateCheckinPayload): Promise<Checkin> {
    const { data } = await api.post<Checkin>("/checkins", payload);
    return data;
  },

  async listMine(): Promise<Checkin[]> {
    const { data } = await api.get<Checkin[]>("/checkins/me");
    return data;
  },

  async get(id: number): Promise<Checkin> {
    const { data } = await api.get<Checkin>(`/checkins/${id}`);
    return data;
  },
};
