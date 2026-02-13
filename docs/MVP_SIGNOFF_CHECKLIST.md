# MVP Signoff Checklist

Минимальный чеклист готовности.

- [ ] `make validate` проходит
- [ ] `make campaign N=10` проходит
- [ ] `make analyze-last-month ...` создает отчет
- [ ] `readiness.ready_for_live_keys` проверен
- [ ] `make realtime-paper ...` пишет `artifacts/realtime/*.jsonl`
- [ ] `PAPER_ONLY=1` включен
- [ ] `make run-live` и `make realtime-live` заблокированы
