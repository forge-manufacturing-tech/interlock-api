import { useState } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { AuthenticationService } from "../api";

export default function ApiKeysPage() {
  const queryClient = useQueryClient();
  const [keyName, setKeyName] = useState("");
  const [newKey, setNewKey] = useState<string | null>(null);
  const [copied, setCopied] = useState(false);

  const { data: keys, isLoading } = useQuery({
    queryKey: ["apiKeys"],
    queryFn: () => AuthenticationService.listApiKeysAuthApiKeysGet(),
  });

  const createMutation = useMutation({
    mutationFn: (name: string) =>
      AuthenticationService.createApiKeyAuthApiKeysPost({ name }),
    onSuccess: (data) => {
      setNewKey(data.key || data.api_key || JSON.stringify(data));
      setKeyName("");
      queryClient.invalidateQueries({ queryKey: ["apiKeys"] });
    },
  });

  const revokeMutation = useMutation({
    mutationFn: (keyId: string) =>
      AuthenticationService.revokeApiKeyAuthApiKeysKeyIdDelete(keyId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["apiKeys"] });
    },
  });

  const handleCreate = (e: React.FormEvent) => {
    e.preventDefault();
    if (!keyName.trim()) return;
    createMutation.mutate(keyName.trim());
  };

  const handleCopy = async (text: string) => {
    await navigator.clipboard.writeText(text);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  return (
    <div className="p-6 space-y-6">
      <div>
        <h1 className="font-mono text-2xl font-bold uppercase tracking-wider text-text-primary">
          API Keys
        </h1>
        <p className="mt-1 text-text-secondary">
          Manage API keys for programmatic access to the Interlock platform.
        </p>
      </div>

      <div className="rounded-md border border-border bg-surface-light p-6 space-y-4">
        <h2 className="font-mono text-sm uppercase tracking-wider text-text-secondary">
          Create New Key
        </h2>
        <form onSubmit={handleCreate} className="flex gap-3">
          <input
            type="text"
            placeholder="Key name (e.g. CI Pipeline)"
            value={keyName}
            onChange={(e) => setKeyName(e.target.value)}
            className="flex-1 rounded-md border border-border bg-surface px-4 py-2.5 text-text-primary placeholder-text-muted outline-none focus:border-primary"
          />
          <button
            type="submit"
            disabled={createMutation.isPending || !keyName.trim()}
            className="rounded-md bg-primary px-4 py-2.5 font-mono text-sm font-medium uppercase tracking-wider text-white transition-colors hover:bg-primary/90 disabled:opacity-50"
          >
            {createMutation.isPending ? "Generating..." : "GENERATE KEY"}
          </button>
        </form>

        {createMutation.isError && (
          <div className="rounded-md border border-red-500/30 bg-red-500/10 px-4 py-3 text-sm text-red-400">
            Failed to create API key. Please try again.
          </div>
        )}
      </div>

      {newKey && (
        <div className="rounded-md border border-yellow-500/30 bg-yellow-500/10 p-6 space-y-3">
          <p className="text-sm font-medium text-yellow-400">
            ⚠ Copy your API key now. It won't be shown again.
          </p>
          <div className="flex items-center gap-2">
            <code className="flex-1 overflow-x-auto rounded-md bg-surface p-3 font-mono text-sm text-text-primary">
              {newKey}
            </code>
            <button
              onClick={() => handleCopy(newKey)}
              className="rounded-md border border-border bg-surface-light px-3 py-2 text-sm text-text-secondary hover:text-text-primary transition-colors"
            >
              {copied ? "Copied!" : "Copy"}
            </button>
          </div>
        </div>
      )}

      <div className="rounded-md border border-border bg-surface-light p-6">
        <h2 className="font-mono text-sm uppercase tracking-wider text-text-secondary mb-4">
          Existing Keys
        </h2>

        {isLoading ? (
          <div className="flex items-center justify-center py-10">
            <div className="h-6 w-6 animate-spin rounded-full border-2 border-primary border-t-transparent" />
          </div>
        ) : !keys || keys.length === 0 ? (
          <p className="text-sm text-text-muted py-4">
            No API keys created yet.
          </p>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full divide-y divide-border">
              <thead>
                <tr>
                  <th className="px-4 py-3 text-left text-xs font-mono uppercase tracking-wider text-text-secondary">
                    Name
                  </th>
                  <th className="px-4 py-3 text-left text-xs font-mono uppercase tracking-wider text-text-secondary">
                    Key
                  </th>
                  <th className="px-4 py-3 text-left text-xs font-mono uppercase tracking-wider text-text-secondary">
                    Created
                  </th>
                  <th className="px-4 py-3 text-left text-xs font-mono uppercase tracking-wider text-text-secondary">
                    Status
                  </th>
                  <th className="px-4 py-3 text-right text-xs font-mono uppercase tracking-wider text-text-secondary">
                    Actions
                  </th>
                </tr>
              </thead>
              <tbody className="divide-y divide-border">
                {keys.map((key) => (
                  <tr key={key.id} className="bg-surface">
                    <td className="px-4 py-3 text-sm text-text-primary">
                      {key.name}
                    </td>
                    <td className="px-4 py-3 text-sm font-mono text-text-muted">
                      ••••{key.last4}
                    </td>
                    <td className="px-4 py-3 text-sm text-text-secondary">
                      {new Date(key.created_at).toLocaleDateString()}
                    </td>
                    <td className="px-4 py-3 text-sm">
                      {key.revoked_at ? (
                        <span className="inline-block rounded-full bg-red-500/20 px-2.5 py-0.5 text-xs font-medium text-red-400">
                          Revoked
                        </span>
                      ) : (
                        <span className="inline-block rounded-full bg-green-500/20 px-2.5 py-0.5 text-xs font-medium text-green-400">
                          Active
                        </span>
                      )}
                    </td>
                    <td className="px-4 py-3 text-right">
                      {!key.revoked_at && (
                        <button
                          onClick={() => revokeMutation.mutate(key.id)}
                          disabled={revokeMutation.isPending}
                          className="rounded-md border border-red-500/30 bg-red-500/10 px-3 py-1.5 text-xs font-medium text-red-400 transition-colors hover:bg-red-500/20 disabled:opacity-50"
                        >
                          Revoke
                        </button>
                      )}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  );
}
