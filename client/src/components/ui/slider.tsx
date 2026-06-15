import * as React from "react";
import { cn } from "@/lib/utils";

export interface SliderProps {
  className?: string;
  value?: number[];
  defaultValue?: number[];
  min?: number;
  max?: number;
  step?: number;
  disabled?: boolean;
  onValueChange?: (value: number[]) => void;
}

const Slider = React.forwardRef<HTMLInputElement, SliderProps>(
  (
    {
      className,
      value,
      defaultValue,
      min = 0,
      max = 100,
      step = 1,
      disabled = false,
      onValueChange,
      ...props
    },
    ref
  ) => {
    const isControlled = value !== undefined;
    const initialValue = defaultValue ? defaultValue[0] : min;
    const [localValue, setLocalValue] = React.useState(initialValue);
    
    // Clamp the active value to stay within [min, max] range to avoid UI/input errors
    let activeValue = isControlled ? (value[0] !== undefined ? value[0] : min) : localValue;
    if (activeValue < min) activeValue = min;
    if (activeValue > max) activeValue = max;

    const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
      const val = parseFloat(e.target.value);
      if (!isControlled) {
        setLocalValue(val);
      }
      if (onValueChange) {
        onValueChange([val]);
      }
    };

    return (
      <div className={cn("relative flex w-full items-center select-none", className)}>
        <input
          ref={ref}
          type="range"
          min={min}
          max={max}
          step={step}
          value={activeValue}
          disabled={disabled}
          onChange={handleChange}
          className="custom-range-slider"
          {...props}
        />
      </div>
    );
  }
);

Slider.displayName = "Slider";

export { Slider };
