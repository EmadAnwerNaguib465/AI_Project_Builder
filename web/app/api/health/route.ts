export const dynamic = "force-dynamic";

export async function GET() {
  try {
    const upstream = await fetch(`${process.env.PLANNER_API_URL ?? "http://127.0.0.1:8000"}/health`, { cache: "no-store" });
    return new Response(await upstream.text(), { status: upstream.status, headers: { "Content-Type": upstream.headers.get("Content-Type") ?? "application/json" } });
  } catch {
    return Response.json({ ok: false, configured: false, detail: "The planner API is unavailable. Start the Python API on port 8000." }, { status: 503 });
  }
}
