export const runtime = "nodejs";
export const dynamic = "force-dynamic";

export async function POST(request: Request) {
  let body: unknown;
  try {
    body = await request.json();
  } catch {
    return Response.json({ detail: "Invalid request body." }, { status: 400 });
  }

  try {
    const upstream = await fetch(`${process.env.PLANNER_API_URL ?? "http://127.0.0.1:8000"}/export/pdf`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(body),
      cache: "no-store",
    });

    if (!upstream.ok) {
      return new Response(await upstream.text(), {
        status: upstream.status,
        headers: { "Content-Type": upstream.headers.get("Content-Type") ?? "application/json" },
      });
    }

    const pdfBuffer = await upstream.arrayBuffer();
    return new Response(pdfBuffer, {
      status: 200,
      headers: {
        "Content-Type": "application/pdf",
        "Content-Disposition": upstream.headers.get("Content-Disposition") ?? 'attachment; filename="project-plan.pdf"',
      },
    });
  } catch {
    return Response.json({ detail: "The export service is unavailable. Ensure the Python API is running." }, { status: 502 });
  }
}
