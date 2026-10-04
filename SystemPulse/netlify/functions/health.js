exports.handler = async () => ({
  statusCode: 200,
  headers: {"content-type":"application/json","cache-control":"no-store"},
  body: JSON.stringify({service:"SystemPulse",status:"online",telemetry:"local-agent"})
});
