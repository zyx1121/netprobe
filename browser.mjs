// Joins the room from real Chromium with livekit-client, once on default
// ICE and once relay-only (TURN), and prints whether each connected.
import { chromium } from "playwright"

const page_html = `<!doctype html><script src="https://cdn.jsdelivr.net/npm/livekit-client@2.15.8/dist/livekit-client.umd.js"></script>`
const browser = await chromium.launch({ args: ["--use-fake-ui-for-media-stream", "--use-fake-device-for-media-stream"] })
for (const relay of [false, true, false, true, true]) {
  const page = await browser.newPage()
  await page.setContent(page_html)
  await page.waitForFunction(() => window.LivekitClient)
  const result = await page.evaluate(async ({ url, token, relay }) => {
    const { Room } = window.LivekitClient
    const room = new Room()
    const t = performance.now()
    try {
      await Promise.race([
        room.connect(url, token, { rtcConfig: relay ? { iceTransportPolicy: "relay" } : {} }),
        new Promise((_, no) => setTimeout(() => no(new Error("timeout 40s")), 40000)),
      ])
      await room.localParticipant.publishData(new TextEncoder().encode("ping"), { reliable: true })
      await new Promise((r) => setTimeout(r, 1500))
      const ms = Math.round(performance.now() - t)
      const stats = await room.engine.pcManager?.publisher?.getStats?.()
      let pair = ""
      stats?.forEach((s) => { if (s.type === "candidate-pair" && s.nominated && s.state === "succeeded") { const l = stats.get(s.localCandidateId); const r = stats.get(s.remoteCandidateId); pair = `${l?.candidateType}/${l?.protocol}${l?.relayProtocol ? "(" + l.relayProtocol + ")" : ""} -> ${r?.address}:${r?.port}` } })
      await room.disconnect()
      return `connected in ${ms} ms via ${pair}`
    } catch (e) {
      return `FAILED after ${Math.round(performance.now() - t)} ms: ${e.message}`
    }
  }, { url: process.env.LK_URL, token: process.env.TOKEN, relay })
  console.log(relay ? "relay  " : "default", result)
  await page.close()
}
await browser.close()
