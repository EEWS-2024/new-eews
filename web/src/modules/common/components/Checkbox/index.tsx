'use client'

import {Checkbox} from "@headlessui/react";

export default function CustomCheckbox({
  checked,
  onChange,
}: {
  checked: boolean
  onChange?: (checked: boolean) => void
}) {
  return (
      <Checkbox
          checked={checked}
          className="group block size-4 rounded border bg-white data-checked:bg-gray-500 cursor-pointer"
          onChange={onChange}
      >
        <svg className="stroke-white opacity-0 group-data-checked:opacity-100" viewBox="0 0 14 14" fill="none">
          <path d="M3 8L6 11L11 3.5" strokeWidth={2} strokeLinecap="round" strokeLinejoin="round" />
        </svg>
      </Checkbox>
  )
}