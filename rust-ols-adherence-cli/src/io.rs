use anyhow::Result;
use csv::ReaderBuilder;

#[derive(Debug, Clone)]
pub struct Row {
    pub x: f64,          // sup_prop
    pub y: f64,          // unsup_prop
    pub unsup_den: Option<usize>,
}

pub fn read_csv(path: &str) -> Result<Vec<Row>> {
    let mut rdr = ReaderBuilder::new().from_path(path)?;
    let mut out = Vec::new();
    for rec in rdr.deserialize() {
        let mut rec: serde_json::Value = rec?;
        // Flexible: read by field names if present
        let x = pick(&mut rec, &["sup_prop", "x", "sup"])?.as_f64().unwrap();
        let y = pick(&mut rec, &["unsup_prop", "y", "unsup"])?.as_f64().unwrap();
        let unsup_den = pick_opt(&mut rec, &["unsup_den", "m", "den"]).and_then(|v| v.as_u64()).map(|u| u as usize);
        out.push(Row { x, y, unsup_den });
    }
    Ok(out)
}

fn pick<'a>(v: &'a mut serde_json::Value, keys: &[&str]) -> anyhow::Result<&'a serde_json::Value> {
    for k in keys {
        if let Some(val) = v.get(*k) { return Ok(val); }
    }
    anyhow::bail!("missing required field; tried {:?}", keys)
}

fn pick_opt<'a>(v: &'a mut serde_json::Value, keys: &[&str]) -> Option<&'a serde_json::Value> {
    for k in keys {
        if let Some(val) = v.get(*k) { return Some(val); }
    }
    None
}
