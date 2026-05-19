import { FormEvent, useState } from "react";
import { Search } from "lucide-react";

type Props = {
  loading: boolean;
  onSearch: (city: string, niche: string, limit: number) => Promise<void>;
};

export default function SearchPanel({ loading, onSearch }: Props) {
  const [city, setCity] = useState("Austin, Texas");
  const [niche, setNiche] = useState("dentist");
  const [limit, setLimit] = useState(10);

  async function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    await onSearch(city, niche, limit);
  }

  return (
    <form onSubmit={submit} className="rounded-lg border border-slate-200 bg-white p-4 shadow-sm">
      <div className="grid gap-3 md:grid-cols-[1fr_1fr_120px_auto]">
        <label className="block">
          <span className="mb-1 block text-sm font-medium text-slate-700">City</span>
          <input
            className="focus-ring w-full rounded-md border border-slate-300 px-3 py-2"
            value={city}
            onChange={(event) => setCity(event.target.value)}
            placeholder="Chicago, Illinois"
            required
          />
        </label>
        <label className="block">
          <span className="mb-1 block text-sm font-medium text-slate-700">Business niche</span>
          <input
            className="focus-ring w-full rounded-md border border-slate-300 px-3 py-2"
            value={niche}
            onChange={(event) => setNiche(event.target.value)}
            placeholder="plumber"
            required
          />
        </label>
        <label className="block">
          <span className="mb-1 block text-sm font-medium text-slate-700">Limit</span>
          <input
            className="focus-ring w-full rounded-md border border-slate-300 px-3 py-2"
            type="number"
            min={1}
            max={50}
            value={limit}
            onChange={(event) => setLimit(Number(event.target.value))}
          />
        </label>
        <button
          className="focus-ring mt-6 flex h-10 items-center justify-center gap-2 rounded-md bg-leaf px-4 font-semibold text-white disabled:cursor-not-allowed disabled:opacity-60 md:min-w-36"
          disabled={loading}
        >
          <Search className="h-4 w-4" />
          {loading ? "Searching" : "Find leads"}
        </button>
      </div>
    </form>
  );
}

