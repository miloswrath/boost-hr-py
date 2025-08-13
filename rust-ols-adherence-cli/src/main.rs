use clap::{Parser, Subcommand, ValueEnum};
use anyhow::Result;
use serde::{Serialize, Deserialize};

mod model;
mod io;

use model::{fit_wls, make_weights, OlsParams, Weighting};

#[derive(Parser)]
#[command(name = "rust-ols-adherence-cli", version)]
struct Cli {
    #[command(subcommand)]
    command: Commands,
}

#[derive(Subcommand)]
enum Commands {
    /// Fit OLS/WLS model from CSV or inline pairs
    Fit(FitArgs),
    /// Predict using a saved model
    Predict(PredictArgs),
}

#[derive(Copy, Clone, Debug, ValueEnum)]
enum WeightsArg { None, N, Binomial }

#[derive(Parser)]
struct FitArgs {
    /// CSV path with columns: sup_prop, unsup_prop, (optional) unsup_den
    #[arg(long)]
    csv: Option<String>,

    /// Inline pairs: "x1:y1,x2:y2,..." where x=sup_prop, y=unsup_prop
    #[arg(long)]
    pairs: Option<String>,

    /// Optional unsupervised denominators for each pair: "m1,m2,..."
    #[arg(long, value_name = "LIST")]
    unsup_dens: Option<String>,

    /// Weighting strategy: none | n | binomial
    #[arg(long, value_enum, default_value_t = WeightsArg::None)]
    weights: WeightsArg,

    /// Output model JSON path
    #[arg(long, default_value = "model.json")]
    out: String,
}

#[derive(Parser)]
struct PredictArgs {
    /// Model JSON path
    #[arg(long)]
    model: String,

    /// x = supervised adherence proportion
    #[arg(long)]
    x: f64,

    /// Confidence level for intervals (e.g., 0.95). If omitted, only point & SE are printed.
    #[arg(long)]
    pi: Option<f64>,
}

#[derive(Serialize, Deserialize)]
struct StoredModel {
    params: OlsParams,
}

fn main() -> Result<()> {
    let cli = Cli::parse();
    match cli.command {
        Commands::Fit(args) => cmd_fit(args),
        Commands::Predict(args) => cmd_predict(args),
    }
}

fn cmd_fit(args: FitArgs) -> Result<()> {
    let (x, y, m_opt): (Vec<f64>, Vec<f64>, Option<Vec<usize>>) = if let Some(path) = args.csv {
        let rows = io::read_csv(&path)?;
        let x: Vec<f64> = rows.iter().map(|r| r.x).collect();
        let y: Vec<f64> = rows.iter().map(|r| r.y).collect();
        let m: Option<Vec<usize>> = if rows.iter().any(|r| r.unsup_den.is_some()) {
            Some(rows.iter().map(|r| r.unsup_den.unwrap_or(0)).collect())
        } else { None };
        (x, y, m)
    } else if let Some(pairs) = args.pairs {
        let mut xs = Vec::new();
        let mut ys = Vec::new();
        for pair in pairs.split(',') {
            let mut it = pair.split(':');
            let x: f64 = it.next().ok_or_else(|| anyhow::anyhow!("bad pair"))?.parse()?;
            let y: f64 = it.next().ok_or_else(|| anyhow::anyhow!("bad pair"))?.parse()?;
            xs.push(x);
            ys.push(y);
        }
        let m = if let Some(dens) = args.unsup_dens {
            Some(dens.split(',').map(|s| s.parse::<usize>()).collect::<Result<Vec<_>, _>>()?)
        } else { None };
        (xs, ys, m)
    } else {
        anyhow::bail!("Provide --csv or --pairs");
    };

    // Choose weighting
    let strategy = match args.weights {
        WeightsArg::None => Weighting::None,
        WeightsArg::N => Weighting::N,
        WeightsArg::Binomial => Weighting::Binomial,
    };

    let w = make_weights(&y, m_opt.as_deref(), strategy)?;
    let params = fit_wls(&x, &y, w.as_deref())?;

    // Save
    let stored = StoredModel { params };
    std::fs::write(&args.out, serde_json::to_vec_pretty(&stored)?)?;

    println!("Fitted model saved to {}", args.out);
    println!("beta0 (intercept): {:.6}", params.beta0);
    println!("beta1 (slope)    : {:.6}", params.beta1);
    println!("sigma^2 (resid)  : {:.6}", params.sigma2);
    println!("n                : {}", params.n);

    Ok(())
}

fn cmd_predict(args: PredictArgs) -> Result<()> {
    let bytes = std::fs::read(&args.model)?;
    let stored: StoredModel = serde_json::from_slice(&bytes)?;
    let p = stored.params;
    let yhat = p.predict(args.x);
    let se_mean = p.se_mean(args.x);
    let se_pred = p.se_pred(args.x);

    println!("x = {:.6}", args.x);
    println!("y_hat = {:.6}", yhat);
    println!("SE(mean) = {:.6}", se_mean);
    println!("SE(pred) = {:.6}", se_pred);

    if let Some(level) = args.pi {
        let z = z_from(level).unwrap_or(1.96);
        let lo = yhat - z * se_pred;
        let hi = yhat + z * se_pred;
        println!("Prediction Interval {:.2}%: [{:.6}, {:.6}]", level * 100.0, lo, hi);
    }

    Ok(())
}

fn z_from(level: f64) -> Option<f64> {
    // crude map for common levels; for other levels, return None → default 1.96
    match (level * 100.0).round() as i32 {
        80 => Some(1.282),
        90 => Some(1.645),
        95 => Some(1.960),
        98 => Some(2.326),
        99 => Some(2.576),
        _ => None,
    }
}
