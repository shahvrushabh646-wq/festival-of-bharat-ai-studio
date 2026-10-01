import React from 'react'; import {cn} from '@/lib/utils';
export const Card=({className='',...p}:React.HTMLAttributes<HTMLDivElement>)=><div className={cn('rounded-xl border bg-white shadow-sm',className)} {...p}/>;
export const CardHeader=({className='',...p}:React.HTMLAttributes<HTMLDivElement>)=><div className={cn('p-6 pb-3',className)} {...p}/>;
export const CardContent=({className='',...p}:React.HTMLAttributes<HTMLDivElement>)=><div className={cn('p-6 pt-3',className)} {...p}/>;
export const CardTitle=({className='',...p}:React.HTMLAttributes<HTMLHeadingElement>)=><h3 className={cn('font-semibold',className)} {...p}/>;