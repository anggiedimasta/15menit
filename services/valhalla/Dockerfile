FROM ghcr.io/gis-ops/docker-valhalla/valhalla:latest

USER root
RUN apt-get update \
    && apt-get install -y --no-install-recommends osmium-tool \
    && rm -rf /var/lib/apt/lists/*

COPY prepare-osm.sh railway-entrypoint.sh /valhalla/scripts/
RUN chmod +x /valhalla/scripts/prepare-osm.sh /valhalla/scripts/railway-entrypoint.sh \
    && chown valhalla:valhalla /valhalla/scripts/prepare-osm.sh /valhalla/scripts/railway-entrypoint.sh

# Entrypoint runs as root to chown Railway volume, then drops to valhalla via runuser.
WORKDIR /custom_files

EXPOSE 8002
ENTRYPOINT ["/valhalla/scripts/railway-entrypoint.sh"]
CMD ["build_tiles"]
