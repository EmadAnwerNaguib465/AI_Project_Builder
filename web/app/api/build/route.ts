export const dynamic = "force-dynamic";

export async function POST(request: Request) {
  try {
    const upstream = await fetch(`${process.env.PLANNER_API_URL ?? "http://127.0.0.1:8000"}/build`, {
      method: "POST", headers: { "Content-Type": "application/json" }, body: await request.text(), cache: "no-store",
    });
    return new Response(upstream.body, { status: upstream.status, headers: { "Content-Type": upstream.headers.get("Content-Type") ?? "application/json", "Cache-Control": "no-cache" } });
  } catch {
    return Response.json({ detail: "The planner API is unavailable. Start the Python API on port 8000." }, { status: 502 });
  }
}
