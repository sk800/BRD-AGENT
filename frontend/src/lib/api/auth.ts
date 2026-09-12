import type { AuthResponse } from "@/types";
import { apiRequest } from "./client";

export async function signup(
  email: string,
  fullName: string,
  password: string,
): Promise<AuthResponse> {
  return apiRequest<AuthResponse>("/api/v1/auth/signup", {
    method: "POST",
    body: JSON.stringify({ email, full_name: fullName, password }),
  });
}

export async function login(
  email: string,
  password: string,
): Promise<AuthResponse> {
  return apiRequest<AuthResponse>("/api/v1/auth/login", {
    method: "POST",
    body: JSON.stringify({ email, password }),
  });
}
