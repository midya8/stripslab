import {audit} from './engine.js';
// Separate linear-frontier counterpart: no heap and no Python search call.
export function auditSearch(task){
 const base=audit(task),states=base.states,n=states.length;
 const vectors={zero:Array(n).fill(0),hmax:states.map(s=>s.hmax.value),hadd:states.map(s=>s.hadd.value),hplus:states.map(s=>s.relaxed.distance)};
 const runs={};
 for(const [mode,values] of Object.entries(vectors)){
  const labels=new Map([[base.initial_mask,{g:0,path:[]}]]),open=new Map([[base.initial_mask,0]]),counts=Array(n).fill(0),steps=[];
  let generated=1,reopened=0,plan=null,cost=null,goal=null;
  const entry=s=>({state:s,g:labels.get(s).g,h:values[s],f:values[s]===null?null:labels.get(s).g+values[s]});
  const order=(a,b)=>(a.f===null?Infinity:a.f)-(b.f===null?Infinity:b.f)||a.g-b.g||a.state-b.state;
  const frontier=()=>Array.from(open.keys(),entry).sort(order);
  while(open.size){
   const queue=frontier(),selected=queue[0],s=selected.state,current=labels.get(s);open.delete(s);
   const step={index:steps.length,frontier:queue,selected,goal:states[s].goal,actions:[]};steps.push(step);
   if(step.goal){plan=current.path.slice();cost=current.g;goal=s;break;}
   counts[s]++;
   for(const edge of states[s].transitions){if(!edge.applicable)continue;
    const t=edge.successor,previous=labels.has(t)?labels.get(t).g:null,candidate=current.g+1,improved=previous===null||candidate<previous,again=improved&&counts[t]>0&&!open.has(t);
    step.actions.push({action:edge.action,target:t,candidate_g:candidate,previous_g:previous,improved,reopened:again});
    if(improved){labels.set(t,{g:candidate,path:[...current.path,edge.action]});open.set(t,candidate);generated++;if(again)reopened++;}
   }
  }
  const admissibility_violations=states.flatMap((s,i)=>s.exact.distance!==null&&(values[i]===null||values[i]>s.exact.distance)?[i]:[]),consistency_violations=[];
  for(let s=0;s<n;s++)for(const e of states[s].transitions)if(e.applicable&&values[e.successor]!==null&&(values[s]===null||values[s]>1+values[e.successor]))consistency_violations.push([s,e.action,e.successor]);
  const optimum=base.initial_exact.distance;
  runs[mode]={values,steps,final_frontier:frontier(),best_g:Array.from({length:n},(_,s)=>labels.has(s)?labels.get(s).g:null),expansion_counts:counts,expansions:counts.reduce((a,b)=>a+b,0),generated,reopened,goal_state:goal,plan,cost,termination:goal===null?'frontier_empty':'goal_popped',exact_optimum:optimum,agrees_with_optimum:cost===optimum,regret:cost===null||optimum===null?null:cost-optimum,admissibility_violations,consistency_violations};
 }
 return {schema:'stripslab-search-v1',input:base.input,base,tie_order:['f_ascending_infinity_last','g_ascending','state_mask_ascending'],runs};
}
