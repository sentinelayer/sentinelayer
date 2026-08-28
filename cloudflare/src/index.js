import { Container, getContainer } from "@cloudflare/containers";

export class SentinelLayerContainer extends Container {
  defaultPort = 8080;
  sleepAfter = "10m";
}

export default {
  async fetch(request, env) {
    const url = new URL(request.url);
    if (url.pathname === "/cloudflare-health") {
      return Response.json({ status: "healthy", service: "sentinellayer-cloudflare" });
    }

    const instance = getContainer(env.SENTINELLAYER_CONTAINER, "primary");
    return instance.fetch(request);
  },
};
