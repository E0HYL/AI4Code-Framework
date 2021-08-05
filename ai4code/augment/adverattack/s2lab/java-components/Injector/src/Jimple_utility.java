import soot.*;
import soot.javaToJimple.LocalGenerator;
import soot.jimple.IdentityStmt;
import soot.jimple.Jimple;
import soot.jimple.NopStmt;
import soot.jimple.ThisRef;
import soot.toolkits.graph.Block;
import soot.toolkits.graph.ExceptionalBlockGraph;
import soot.toolkits.graph.ExceptionalUnitGraph;

import java.util.ArrayList;
import java.util.Iterator;
import java.util.List;

public class Jimple_utility {
    public void removeStatement(Unit u, Body body){
        body.getUnits().remove(u);
    }


    public NopStmt insertNopBeforeStmt(Body body, Unit u){
        NopStmt nop = Jimple.v().newNopStmt();
        body.getUnits().insertBefore(nop, u);
        return nop;
    }

    public Local generateNewLocal(Body body, Type type){
        LocalGenerator lg = new LocalGenerator(body);
        return lg.generateLocal(type);
    }


    public int calculate_cyclomatic_complexity(SootClass c){
        int out = 0;

        for(SootMethod m : c.getMethods()){
            if(!m.hasActiveBody()){
                continue;
            }else{
                int edges, nodes,tmp_result;
                Body b = m.getActiveBody();
                ExceptionalUnitGraph CFG = new ExceptionalUnitGraph(b);
                ExceptionalBlockGraph BFG = new ExceptionalBlockGraph(CFG);
                Block first =BFG.getHeads().get(0);
                edges = get_edges(new ArrayList<Block>() ,first);

                nodes = BFG.size();
                tmp_result = edges-nodes+2;
                out+=tmp_result;
            }
        }
        if(out<0){
            out =0;
        }


        return out;
    }

    public int get_edges(ArrayList<Block> to_avoid, Block start){
        List<Block> tmp =start.getSuccs();
        to_avoid.add(start);
        if(tmp.isEmpty()){
            return 0;
        }else{
            int result= tmp.size();
            for(Block b : tmp){
                if(!to_avoid.contains(b)) {
                    to_avoid.add(b);
                    result += get_edges(to_avoid, b);
                }
            }
            return result;
        }
    }


    private boolean in_Locals(Value to_check,ArrayList<Local> locals){
        for(Local  l: locals){
            if(l.equals(to_check)){
                return true;
            }
        }
        return false;
    }


    public ArrayList<Unit> clear_Unit_list(UnitPatchingChain units,ArrayList<Local> to_slice){
        ArrayList<Unit> to_ret = new ArrayList<>();
        for(Iterator<Unit> iter = units.iterator(); iter.hasNext();) {
            Unit u = iter.next();
            if (!(u instanceof ThisRef)) {
                boolean to_add = true;
                for(ValueBox vb : u.getUseAndDefBoxes()){
                    if(vb.getValue() instanceof Local){
                        if(!in_Locals(vb.getValue(),to_slice)){
                            to_add= false;
                        }
                    }
                }
                if(to_add) to_ret.add(u);
            }
        }
        return  to_ret;
    }

    public ArrayList<Unit> clear_Unit_list(UnitPatchingChain units){
        ArrayList<Unit> to_ret = new ArrayList<>();
        for(Iterator<Unit> iter = units.iterator(); iter.hasNext();) {
            Unit u = iter.next();
            if (!(u instanceof IdentityStmt)) {
                    to_ret.add(u);

            }
        }
        return  to_ret;
    }
    public ArrayList<Unit> clear_Unit_list(ArrayList<Unit> units){
        ArrayList<Unit> to_ret = new ArrayList<>();
        for(Iterator<Unit> iter = units.iterator(); iter.hasNext();) {
            Unit u = iter.next();
            if (!(u instanceof IdentityStmt)) {
                    to_ret.add(u);

            }
        }
        return  to_ret;
    }


    public ArrayList<Unit> clear_Unit_list(ArrayList<Unit> units,ArrayList<Local> to_slice){
        ArrayList<Unit> to_ret = new ArrayList<>();
        for(Iterator<Unit> iter = units.iterator(); iter.hasNext();) {
            Unit u = iter.next();
            if (!(u instanceof IdentityStmt)) {
                boolean to_add = true;
                for(ValueBox vb : u.getUseAndDefBoxes()){
                    if(vb.getValue() instanceof Local){
                        if(!in_Locals(vb.getValue(),to_slice)){
                            to_add= false;
                        }
                    }
                }
                if(to_add) to_ret.add(u);
            }
        }
        return  to_ret;
    }



    public ArrayList<Local> clear_Local_list(ArrayList<Local> locals,String name){
        ArrayList<Local> to_ret = new ArrayList<>();
        for(Iterator<Local> iter = locals.iterator(); iter.hasNext();){
            Local u = iter.next();
            if(!(u.getType().toString().startsWith("Slice")) && !(u.getType().toString().contains("bottom_type") && u.getName() != "this")) {
                to_ret.add(u);
            }else if (u.getType().toString().contains("bottom_type") && name.length()>0){
                Type t = RefType.v(name);
                u.setType(t);
                to_ret.add(u);
            }else{
                continue;
            }
        }
        return  to_ret;
    }
}
