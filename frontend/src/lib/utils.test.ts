import { describe, expect, it } from 'vitest';
import { cn } from './utils';

describe('cn utility', () => {
  it('merges basic class names', () => {
    expect(cn('class1', 'class2')).toBe('class1 class2');
  });

  it('handles conditional classes', () => {
    expect(cn({ 'class1': true, 'class2': false, 'class3': true })).toBe('class1 class3');
  });

  it('resolves conflicting tailwind classes via twMerge', () => {
    // text-blue-500 should override text-red-500
    expect(cn('text-red-500', 'text-blue-500')).toBe('text-blue-500');
    // p-4 overrides px-2 and py-1
    expect(cn('px-2 py-1', 'p-4')).toBe('p-4');
  });

  it('handles arrays of classes', () => {
    expect(cn(['class1', 'class2'], ['class3'])).toBe('class1 class2 class3');
  });

  it('ignores falsy values', () => {
    expect(cn('class1', null, undefined, false, 0, '', 'class2')).toBe('class1 class2');
  });

  it('handles complex combinations', () => {
    expect(
      cn(
        'base-class',
        { 'conditional-class': true, 'ignored-class': false },
        ['array-class', 'text-red-500'],
        null,
        'text-blue-500' // Should override text-red-500
      )
    ).toBe('base-class conditional-class array-class text-blue-500');
  });
});
