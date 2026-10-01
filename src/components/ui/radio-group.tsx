import React from 'react';
const Ctx=React.createContext<{value:string,onValueChange:(v:string)=>void}>({value:'',onValueChange:()=>{}});
export function RadioGroup({value,onValueChange,children,className}:any){return <Ctx.Provider value={{value,onValueChange}}><div className={className}>{children}</div></Ctx.Provider>}
export function RadioGroupItem({value,id,...p}:any){const c=React.useContext(Ctx); return <input type="radio" id={id} value={value} checked={c.value===value} onChange={()=>c.onValueChange(value)} {...p}/>