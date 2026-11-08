// Reads the processor time on a real Windows with the same command the aeprogress plugin
// runs, and checks that the plugin's own parser reads what typeperf printed.
import { execFileSync } from 'node:child_process'

import { windowsMachine } from '../../integrations/claude-code/aeprogress/hooks/machine.ts'

const out = execFileSync('typeperf', ['\\Processor(_Total)\\% Processor Time', '-sc', '1'], { encoding: 'utf8' })
console.log(out)
const machine = windowsMachine(out)
console.log('parsed:', JSON.stringify(machine))
if (!machine || !(machine.busy >= 0 && machine.busy <= 1.5)) {
  console.error('the plugin did not read the processor time from typeperf')
  process.exit(1)
}
