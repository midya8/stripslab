import {audit} from './engine.js';
// Independent all-state synchronous distance sweeps and BigInt DAG counts.
export function auditSensitivity(task){
 const base=audit(task),states=base.states,n=states.length,m=base.input.actions.length,full=2**m-1,start=base.initial_mask,goals=states.filter(s=>s.goal).map(s=>s.mask),scenarios=[];
 for(let enabled=0;enabled<=full;enabled++){
  const edges=states.flatMap(s=>s.transitions.filter(t=>t.applicable&&(enabled&(1<<t.action))).map(t=>({source:s.mask,action:t.action,target:t.successor})));
  let forward=Array(n).fill(null),backward=states.map(s=>s.goal?0:null);forward[start]=0;
  for(let pass=0;pass<n;pass++){
   const f=forward.slice(),b=backward.slice();
   for(const e of edges){if(forward[e.source]!==null&&(f[e.target]===null||forward[e.source]+1<f[e.target]))f[e.target]=forward[e.source]+1;if(backward[e.target]!==null&&(b[e.source]===null||backward[e.target]+1<b[e.source]))b[e.source]=backward[e.target]+1;}
   const same=f.every((v,i)=>v===forward[i])&&b.every((v,i)=>v===backward[i]);forward=f;backward=b;if(same)break;
  }
  const count=Array(n).fill(0n);count[start]=1n;
  for(let depth=0;depth<n;depth++)for(const e of edges)if(forward[e.source]===depth&&forward[e.target]===depth+1)count[e.target]+=count[e.source];
  const distance=backward[start],optimal_edges=distance===null?[]:edges.filter(e=>forward[e.source]!==null&&backward[e.target]!==null&&forward[e.source]+1+backward[e.target]===distance);
  let representative=null;
  if(distance!==null){representative=[];let s=start;for(let k=0;k<distance;k++){const e=edges.find(e=>e.source===s&&backward[e.target]!==null&&backward[e.target]+1===backward[s]);representative.push(e.action);s=e.target;}}
  scenarios.push({enabled_mask:enabled,enabled_actions:Array.from({length:m},(_,a)=>a).filter(a=>enabled&(1<<a)),removed_actions:Array.from({length:m},(_,a)=>a).filter(a=>!(enabled&(1<<a))),distance,plan_count:distance===null?'0':String(goals.filter(g=>forward[g]===distance).reduce((v,g)=>v+count[g],0n)),representative,distances_from_initial:forward,distances_to_goal:backward,shortest_prefix_counts:count.map(String),optimal_edges});
 }
 const baseline=scenarios[full],solved=baseline.distance!==null;
 const minima=predicate=>scenarios.map(s=>s.enabled_mask).filter(mask=>predicate(mask)&&Array.from({length:m},(_,a)=>a).filter(a=>mask&(1<<a)).every(a=>!predicate(mask^(1<<a))));
 return {schema:'stripslab-sensitivity-v1',input:base.input,base,baseline_enabled_mask:full,scenarios,minimal_sufficient_enabled:minima(mask=>scenarios[mask].distance!==null),minimal_optimal_enabled:solved?minima(mask=>scenarios[mask].distance===baseline.distance):null,minimal_solvability_cuts:solved?minima(mask=>scenarios[full^mask].distance===null):null,minimal_optimality_cuts:solved?minima(mask=>scenarios[full^mask].distance!==baseline.distance):null,single_removals:Array.from({length:m},(_,a)=>({action:a,enabled_mask:full^(1<<a),used_by_representative:solved?baseline.representative.includes(a):null,necessary_for_optimality:solved?scenarios[full^(1<<a)].distance!==baseline.distance:null,necessary_for_solvability:solved?scenarios[full^(1<<a)].distance===null:null})),baseline_solvable:solved};
}
