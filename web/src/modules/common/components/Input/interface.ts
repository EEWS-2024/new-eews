import { InputHTMLAttributes } from 'react'

export interface InputInterface extends InputHTMLAttributes<HTMLInputElement> {
  errorMessage?: string
}
