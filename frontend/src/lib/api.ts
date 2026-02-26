import type { AskResponse, Poll } from '@/types';

const API_BASE =
  process.env.NEXT_PUBLIC_API_URL ?? 'http://localhost:8000/api/v1';

export async function askQuestion(question: string): Promise<AskResponse> {
  const res = await fetch(`${API_BASE}/ask`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ question }),
  });
  if (!res.ok) throw new Error(`Ask request failed (${res.status})`);
  return res.json();
}

export async function fetchPolls(): Promise<Poll[]> {
  const res = await fetch(`${API_BASE}/polls`);
  if (!res.ok) throw new Error(`Failed to fetch polls (${res.status})`);
  return res.json();
}

export async function fetchActivePoll(): Promise<Poll> {
  const res = await fetch(`${API_BASE}/polls/active`);
  if (!res.ok) throw new Error(`No active poll found (${res.status})`);
  return res.json();
}

export async function voteInPoll(
  pollId: number,
  optionId: number,
  fingerprint?: string,
): Promise<Poll> {
  const res = await fetch(`${API_BASE}/polls/${pollId}/vote`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ option_id: optionId, fingerprint }),
  });
  if (!res.ok) {
    const body = await res.json().catch(() => null);
    throw new Error(body?.detail ?? `Vote failed (${res.status})`);
  }
  return res.json();
}
