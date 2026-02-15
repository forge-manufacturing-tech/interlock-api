import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { AuthenticationService } from "../api";
import type { UserRead, UserUpdate } from "../api";
import { Shield, Bot, ShieldOff, UserPlus, Users } from "lucide-react";
import { useAuth } from "../lib/auth";

export default function AdminPage() {
  const { user: currentUser } = useAuth();
  const queryClient = useQueryClient();

  const { data: users, isLoading } = useQuery({
    queryKey: ["admin-users"],
    queryFn: () => AuthenticationService.listUsersAuthAdminUsersGet(),
  });

  const { data: settings } = useQuery({
    queryKey: ["system-settings"],
    queryFn: () => AuthenticationService.getSystemSettingsAuthSettingsGet(),
  });

  const updateMutation = useMutation({
    mutationFn: ({ userId, data }: { userId: string; data: UserUpdate }) =>
      AuthenticationService.updateUserAuthAdminUsersUserIdPatch(userId, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["admin-users"] });
    },
  });

  const settingsMutation = useMutation({
    mutationFn: (data: { key: string; value: boolean }) =>
      AuthenticationService.updateSystemSettingAuthAdminSettingsPatch(data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["system-settings"] });
    },
  });

  const toggleAi = (user: UserRead) => {
    updateMutation.mutate({
      userId: user.id,
      data: { ai_enabled: !user.ai_enabled },
    });
  };

  const toggleRole = (user: UserRead) => {
    updateMutation.mutate({
      userId: user.id,
      data: { role: user.role === "admin" ? "member" : "admin" },
    });
  };

  const toggleSetting = (key: string, currentValue: boolean | undefined) => {
    settingsMutation.mutate({ key, value: !(currentValue ?? true) });
  };

  return (
    <div className="space-y-6">
      <div>
        <h1 className="font-mono text-2xl font-bold uppercase tracking-wider text-text-primary">
          User Management
        </h1>
        <p className="mt-1 text-text-secondary">
          Manage user roles, AI access, and system-wide signup settings.
        </p>
      </div>

      {settings && (
        <div className="rounded-md border border-border bg-surface-light p-5 space-y-4">
          <h2 className="font-mono text-sm font-semibold uppercase tracking-wider text-text-secondary">
            System Settings
          </h2>
          <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
            <div className="flex items-center justify-between rounded-md border border-border bg-surface px-4 py-3">
              <div className="flex items-center gap-3">
                <UserPlus className="h-5 w-5 text-text-muted" />
                <div>
                  <p className="text-sm font-medium text-text-primary">Open Signups</p>
                  <p className="text-xs text-text-muted">Allow new users to create accounts</p>
                </div>
              </div>
              <button
                onClick={() => toggleSetting("signup_enabled", settings.signup_enabled)}
                disabled={settingsMutation.isPending}
                className={`relative inline-flex h-6 w-11 flex-shrink-0 cursor-pointer rounded-full border-2 border-transparent transition-colors duration-200 focus:outline-none disabled:opacity-50 ${
                  settings.signup_enabled ? "bg-primary" : "bg-zinc-600"
                }`}
              >
                <span
                  className={`pointer-events-none inline-block h-5 w-5 transform rounded-full bg-white shadow transition duration-200 ${
                    settings.signup_enabled ? "translate-x-5" : "translate-x-0"
                  }`}
                />
              </button>
            </div>
            <div className="flex items-center justify-between rounded-md border border-border bg-surface px-4 py-3">
              <div className="flex items-center gap-3">
                <Users className="h-5 w-5 text-text-muted" />
                <div>
                  <p className="text-sm font-medium text-text-primary">New Users Are Admin</p>
                  <p className="text-xs text-text-muted">Grant admin role to all new signups</p>
                </div>
              </div>
              <button
                onClick={() => toggleSetting("new_users_are_admin", settings.new_users_are_admin)}
                disabled={settingsMutation.isPending}
                className={`relative inline-flex h-6 w-11 flex-shrink-0 cursor-pointer rounded-full border-2 border-transparent transition-colors duration-200 focus:outline-none disabled:opacity-50 ${
                  settings.new_users_are_admin ? "bg-primary" : "bg-zinc-600"
                }`}
              >
                <span
                  className={`pointer-events-none inline-block h-5 w-5 transform rounded-full bg-white shadow transition duration-200 ${
                    settings.new_users_are_admin ? "translate-x-5" : "translate-x-0"
                  }`}
                />
              </button>
            </div>
          </div>
        </div>
      )}

      <div className="rounded-md border border-border bg-surface-light">
        {isLoading ? (
          <div className="flex items-center justify-center py-16">
            <div className="h-8 w-8 animate-spin rounded-full border-2 border-primary border-t-transparent" />
          </div>
        ) : !users || users.length === 0 ? (
          <div className="p-8 text-center text-text-muted">No users found.</div>
        ) : (
          <table className="w-full">
            <thead>
              <tr className="border-b border-border text-left text-xs font-mono uppercase tracking-wider text-text-muted">
                <th className="px-4 py-3">User</th>
                <th className="px-4 py-3">Role</th>
                <th className="px-4 py-3">AI Access</th>
                <th className="px-4 py-3">Joined</th>
                <th className="px-4 py-3 text-right">Actions</th>
              </tr>
            </thead>
            <tbody>
              {users.map((u) => {
                const isSelf = u.id === currentUser?.id;
                return (
                  <tr
                    key={u.id}
                    className="border-b border-border/50 last:border-0"
                  >
                    <td className="px-4 py-3">
                      <div>
                        <p className="text-sm font-medium text-text-primary">
                          {u.name || u.email}
                        </p>
                        <p className="text-xs text-text-muted">{u.email}</p>
                      </div>
                    </td>
                    <td className="px-4 py-3">
                      <span
                        className={`inline-flex items-center gap-1 rounded-full px-2.5 py-0.5 text-xs font-medium ${
                          u.role === "admin"
                            ? "border border-primary/40 bg-primary/10 text-primary"
                            : "border border-border bg-surface text-text-secondary"
                        }`}
                      >
                        {u.role === "admin" ? (
                          <Shield size={12} />
                        ) : (
                          <ShieldOff size={12} />
                        )}
                        {u.role}
                      </span>
                    </td>
                    <td className="px-4 py-3">
                      <span
                        className={`inline-flex items-center gap-1 rounded-full px-2.5 py-0.5 text-xs font-medium ${
                          u.ai_enabled || u.role === "admin"
                            ? "border border-green-500/40 bg-green-500/10 text-green-400"
                            : "border border-red-500/40 bg-red-500/10 text-red-400"
                        }`}
                      >
                        <Bot size={12} />
                        {u.role === "admin"
                          ? "Always on"
                          : u.ai_enabled
                            ? "Enabled"
                            : "Disabled"}
                      </span>
                    </td>
                    <td className="px-4 py-3 text-xs text-text-muted">
                      {new Date(u.created_at).toLocaleDateString()}
                    </td>
                    <td className="px-4 py-3 text-right">
                      <div className="flex items-center justify-end gap-2">
                        {!isSelf && u.role !== "admin" && (
                          <button
                            onClick={() => toggleAi(u)}
                            disabled={updateMutation.isPending}
                            className={`rounded-md border px-3 py-1.5 text-xs font-medium transition-colors ${
                              u.ai_enabled
                                ? "border-red-500/40 text-red-400 hover:bg-red-500/10"
                                : "border-green-500/40 text-green-400 hover:bg-green-500/10"
                            } disabled:opacity-50`}
                          >
                            {u.ai_enabled ? "Disable AI" : "Enable AI"}
                          </button>
                        )}
                        {!isSelf && (
                          <button
                            onClick={() => toggleRole(u)}
                            disabled={updateMutation.isPending}
                            className="rounded-md border border-border px-3 py-1.5 text-xs font-medium text-text-secondary transition-colors hover:border-primary hover:text-primary disabled:opacity-50"
                          >
                            {u.role === "admin"
                              ? "Demote to Member"
                              : "Promote to Admin"}
                          </button>
                        )}
                        {isSelf && (
                          <span className="text-xs text-text-muted italic">
                            You
                          </span>
                        )}
                      </div>
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        )}
      </div>
    </div>
  );
}
