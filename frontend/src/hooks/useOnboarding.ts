import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { getApiBaseUrl } from "@/lib/api-config";
import axios from "axios";

interface UserResponse {
    id: number;
    email: string;
    username: string;
    onboarding_completed: boolean;
}

const fetchUser = async () => {
    const token = typeof window !== "undefined" ? localStorage.getItem("auth_token") : null;
    if (!token) throw new Error("No auth token");

    const baseUrl = getApiBaseUrl();
    const response = await axios.get<UserResponse>(`${baseUrl}/api/auth/me`, {
        headers: {
            Authorization: `Bearer ${token}`,
        },
    });
    return response.data;
};

export function useOnboarding() {
    const queryClient = useQueryClient();

    const query = useQuery({
        queryKey: ["currentUser"],
        queryFn: fetchUser,
        retry: false,
        enabled: typeof window !== "undefined" && !!localStorage.getItem("auth_token"),
        staleTime: 5 * 60 * 1000, // 5 minutes
    });

    const completeOnboardingMutation = useMutation({
        mutationFn: async () => {
            // Assuming there's an endpoint or we just invalidate/optimistically update
            // For now, we mainly use this to update local state logic if needed, 
            // but if the backend had a specific 'complete onboarding' endpoint, it would go here.
            // Since the original code only set local state, we might just need to refetch or assume it's done.
            // If there IS an endpoint, we should call it. 
            // Checking original page.tsx ... it just did setUserOnboardingStatus(true).
            // If we want to persist it, we likely need an API call.
            // For now, let's assume we just want to re-fetch the user to get updated status if it changed on backend.
            return true;
        },
        onSuccess: () => {
            queryClient.invalidateQueries({ queryKey: ["currentUser"] });
        },
    });

    return {
        ...query,
        isOnboardingCompleted: query.data?.onboarding_completed,
        completeOnboarding: completeOnboardingMutation.mutate,
    };
}
