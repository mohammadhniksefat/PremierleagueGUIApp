FROM fluent/fluentd:v1.16-1

USER root
RUN gem install fluent-plugin-loki

COPY fluent.conf /fluentd/etc/fluent.conf