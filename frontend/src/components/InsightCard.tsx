import React, { ReactNode } from 'react';
import { Card, CardHeader, CardTitle, CardContent, CardFooter } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { AlertCircle, RefreshCw, Info } from "lucide-react";

export interface InsightCardProps {
  title: string;
  icon?: ReactNode;
  loading?: boolean;
  error?: string | null;
  empty?: boolean;
  emptyMessage?: string;
  onRetry?: () => void;
  provenance?: string;
  children: ReactNode;
  footerActions?: ReactNode;
}

export function InsightCard({
  title,
  icon,
  loading,
  error,
  empty,
  emptyMessage = "데이터가 없습니다.",
  onRetry,
  provenance,
  children,
  footerActions,
}: InsightCardProps) {
  return (
    <Card className="flex flex-col h-full bg-white/50 backdrop-blur-xl border-white/20 shadow-[0_8px_32px_-8px_rgba(37,99,255,0.08)]">
      <CardHeader className="pb-3 pt-4 px-4 flex flex-row items-center justify-between space-y-0 bg-gradient-to-r from-primary/5 to-transparent border-b border-primary/5">
        <CardTitle className="text-sm font-bold flex items-center gap-2">
          {icon && <span className="text-primary">{icon}</span>}
          {title}
        </CardTitle>
        {provenance && (
          <div className="flex items-center text-[10px] text-muted-foreground bg-white/60 px-2 py-1 rounded-full border border-primary/10 shadow-sm" title="출처/사용된 모델">
            <Info className="w-3 h-3 mr-1 text-primary/70" />
            {provenance}
          </div>
        )}
      </CardHeader>
      
      <CardContent className="flex-1 p-4 overflow-auto">
        {loading ? (
          <div className="flex flex-col items-center justify-center h-32 space-y-3">
            <div className="relative flex items-center justify-center">
              <div className="absolute inset-0 border-t-2 border-primary rounded-full animate-spin w-8 h-8 opacity-70"></div>
              <div className="absolute inset-2 bg-primary/20 rounded-full blur-sm"></div>
            </div>
            <span className="text-xs text-muted-foreground font-medium tracking-wide">AI가 분석 중입니다...</span>
          </div>
        ) : error ? (
          <div className="flex flex-col items-center justify-center h-32 text-center space-y-3 p-4 bg-red-50/50 rounded-xl border border-red-100">
            <div className="bg-red-100 p-2 rounded-full">
              <AlertCircle className="w-5 h-5 text-red-500" />
            </div>
            <span className="text-sm text-red-600 font-medium">{error}</span>
            {onRetry && (
              <Button variant="outline" size="sm" onClick={onRetry} className="mt-2 h-8 text-xs bg-white hover:bg-red-50 hover:text-red-600 border-red-200">
                <RefreshCw className="w-3 h-3 mr-1.5" /> 다시 시도
              </Button>
            )}
          </div>
        ) : empty ? (
          <div className="flex items-center justify-center h-32 text-sm text-muted-foreground bg-secondary/30 rounded-xl border border-dashed border-border/60">
            {emptyMessage}
          </div>
        ) : (
          <div className="text-sm text-foreground leading-relaxed">
            {children}
          </div>
        )}
      </CardContent>

      {footerActions && !loading && !error && !empty && (
        <CardFooter className="pt-3 pb-3 px-4 border-t border-border/50 bg-secondary/10 flex justify-end gap-2">
          {footerActions}
        </CardFooter>
      )}
    </Card>
  );
}
