import React from 'react'; import {cn} from '@/lib/utils';
const Ctx=React.createContext<{value:string,onValueChange:(v:string)=>void}>({value:'',onValueChange:()=>{}});
export function Select({value,onValueChange,children}:any){return <Ctx.Provider value={{value,onValueChange}}><div className="relative">{children}</div></Ctx.Provider>}
export function SelectTrigger({children,className='',...p}:any){const c=React.useContext(Ctx);return <div className={cn('relative',className)}><select aria-label="Select" className={cn('w-full appearance-none rounded-lg border bg-white px-3 py-2 pr-8 text-sm')} value={c.value} onChange={e=>c.onValueChange(e.target.value)} {...p}>{children}</select></div>}
export function SelectValue({placeholder}:any){return <option value="" disabled>{placeholder}</option>}
export function SelectContent({children}:any){return <>{children}</>}
export function SelectItem({value,children}:any){return <option value={value}>{children}</option>}