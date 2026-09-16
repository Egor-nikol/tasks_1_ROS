# syntax=docker/dockerfile:1
# The instructor freezes the published manifest digest before distribution.
ARG ROS_BASE=ros:jazzy-ros-base-noble
FROM ${ROS_BASE}
ARG CODE_SERVER_VERSION=4.104.2
ARG COURSE_RELEASE=2026.1-l01-rc2
ARG TARGETARCH
ENV DEBIAN_FRONTEND=noninteractive
SHELL ["/bin/bash", "-o", "pipefail", "-c"]
RUN apt-get update && apt-get install -y --no-install-recommends \
    ros-jazzy-turtlesim ros-jazzy-rmw-cyclonedds-cpp \
    ros-jazzy-launch-testing ros-jazzy-launch-testing-ament-cmake \
    ros-jazzy-ament-lint-auto ros-jazzy-rosidl-default-generators \
    ros-jazzy-ament-cmake ros-jazzy-action-msgs \
    python3-pytest python3-yaml python3-colcon-common-extensions \
    build-essential cmake git curl ca-certificates openssh-client \
    procps iproute2 xvfb xauth libatomic1 libstdc++6 passwd \
    && rm -rf /var/lib/apt/lists/*
# Versioned upstream binary. Image digest freezes the actual installed dependencies.
RUN arch="${TARGETARCH:-$(dpkg --print-architecture)}" && \
    curl --fail --location --retry 3 \
      "https://github.com/coder/code-server/releases/download/v${CODE_SERVER_VERSION}/code-server_${CODE_SERVER_VERSION}_${arch}.deb" \
      -o /tmp/code-server.deb && \
    sha256sum /tmp/code-server.deb > /opt/code-server-download.sha256 && \
    apt-get update && apt-get install -y --no-install-recommends /tmp/code-server.deb && \
    rm /tmp/code-server.deb && rm -rf /var/lib/apt/lists/*
WORKDIR /opt/course_ws
COPY src/shad_interfaces src/shad_interfaces
COPY src/course_lab src/course_lab
RUN source /opt/ros/jazzy/setup.bash && colcon build --merge-install && rm -rf build log
COPY tools /opt/course_tools
COPY docker/entrypoint.sh /usr/local/bin/course-entrypoint
COPY docker/course-internal /usr/local/bin/course
RUN chmod 755 /usr/local/bin/course-entrypoint /usr/local/bin/course && \
    dpkg-query -W -f='${binary:Package}\t${Version}\n' > /opt/course-packages.lock && \
    printf '%s\n' "${COURSE_RELEASE}" > /opt/course-release.txt && \
    mkdir -p /workspace /home/student && chmod 1777 /workspace /home/student
ENV COURSE_RELEASE=${COURSE_RELEASE} \
    RMW_IMPLEMENTATION=rmw_cyclonedds_cpp \
    ROS_AUTOMATIC_DISCOVERY_RANGE=LOCALHOST ROS_DOMAIN_ID=42 PYTHONUNBUFFERED=1 HOME=/home/student \
    CYCLONEDDS_URI=file:///opt/course_tools/cyclonedds.xml
# A passwd entry avoids IDE tooling assuming an unknown uid on minimal base images.
RUN if ! getent group 1000 >/dev/null; then groupadd --gid 1000 student; fi && \
    if ! getent passwd 1000 >/dev/null; then useradd --uid 1000 --gid 1000 --home-dir /home/student --shell /bin/bash student; fi
USER 1000:1000
WORKDIR /workspace
ENTRYPOINT ["/usr/local/bin/course-entrypoint"]
CMD ["course", "dev"]
