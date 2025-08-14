use anyhow::{Context, Result};
use csv::{ReaderBuilder, Trim};

#[derive(Debug, Clone)]
pub struct Row {
    pub x: f64,          // sup_prop
    pub y: f64,          // unsup_prop
    pub unsup_den: Option<usize>,
}

pub fn read_csv(path: &str) -> Result<Vec<Row>> {
    let mut rdr = ReaderBuilder::new()
        .has_headers(true)
        .trim(Trim::All)
        .flexible(true)            // tolerate ragged rows
        .from_path(path)
        .with_context(|| format!("opening {}", path))?;

    // Capture headers (if present)
    let headers = rdr.headers()?.clone();

    // normalize: trim + strip BOM + lowercase
    let norm = |s: &str| s.trim().trim_start_matches('\u{feff}').to_ascii_lowercase();

    // find first matching header index from a list of candidate names
    let find_idx = |candidates: &[&str]| {
        let mut first = None;
        for (i, h) in headers.iter().enumerate() {
            let h = norm(h);
            if candidates.iter().any(|c| h == c.to_ascii_lowercase()) {
                first = Some(i);
                break;
            }
        }
        first
    };

    // preferred header names (in order) and positional fallbacks
    let xi = find_idx(&["sup_prop", "x", "sup"]).or(Some(0)); // fallback: col 0
    let yi = find_idx(&["unsup_prop", "y", "unsup"]).or(Some(1)); // fallback: col 1
    let di = find_idx(&["unsup_den", "m", "den"]); // optional, no positional fallback

    let mut out = Vec::new();
    for rec in rdr.records() {
        let rec = rec?;
        let get = |i: usize| rec.get(i).map(str::trim).unwrap_or("");

        let x_str = xi.ok_or_else(|| anyhow::anyhow!("missing required field; tried {:?}", ["sup_prop","x","sup"]))?;
        let y_str = yi.ok_or_else(|| anyhow::anyhow!("missing required field; tried {:?}", ["unsup_prop","y","unsup"]))?;

        let x: f64 = get(x_str).parse()
            .with_context(|| format!("parsing x from field {} value {:?}", x_str, get(x_str)))?;
        let y: f64 = get(y_str).parse()
            .with_context(|| format!("parsing y from field {} value {:?}", y_str, get(y_str)))?;

        let unsup_den = di.and_then(|i| get(i).parse::<usize>().ok());

        out.push(Row { x, y, unsup_den });
    }

    Ok(out)
}

