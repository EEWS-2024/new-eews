import React, { forwardRef } from 'react'
import { twMerge } from 'tailwind-merge'
import { InputInterface } from '@/modules/common/components/Input/interface'

export const Input = forwardRef<HTMLInputElement, InputInterface>(
  ({ className, errorMessage, ...props }, ref) => {
    return (
      <div className={'flex gap-1 flex-col w-full'}>
        <input
          ref={ref}
          className={twMerge(
            'block w-full rounded-lg border-none bg-white/5 py-1.5 px-3 text-sm/6 text-white focus:outline-none data-[focus]:outline-2 data-[focus]:-outline-offset-2 data-[focus]:outline-white/25',
            className
          )}
          {...props}
        />
        {errorMessage && (
          <small className={'text-red-400'}>{errorMessage}</small>
        )}
      </div>
    )
  }
)
