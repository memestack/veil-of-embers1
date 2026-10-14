/** Generic pool: avoids allocation/GC during hordes. */
export class Pool<T> {
  private free: T[] = [];
  constructor(private readonly factory: () => T) {}
  get(): T {
    return this.free.pop() ?? this.factory();
  }
  release(item: T): void {
    this.free.push(item);
  }
  get size(): number {
    return this.free.length;
  }
}
