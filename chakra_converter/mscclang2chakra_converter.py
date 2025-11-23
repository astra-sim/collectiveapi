#!/usr/bin/env python3

import logging

from  xml.etree import ElementTree
from typing import Any, List
from chakra.src.third_party.utils.protolib import encodeMessage as encode_message
from chakra.schema.protobuf.et_def_pb2 import (
    NodeType,
    Node,
    AttributeProto as ChakraAttr,
    COMP_NODE,
    COMM_COLL_NODE,
    ALL_REDUCE,
    ALL_TO_ALL,
    ALL_GATHER,
    REDUCE_SCATTER,
    COMM_SEND_NODE,
    COMM_RECV_NODE,
    GlobalMetadata
)


class MSCCLStep:    
    def add_parent(
        self,
        parent: "MSCCLStep",
    ) -> None: 
        if type(parent) is MSCCLNopStep:
            raise Exception(f"Nop parent added as parent")
        if type(self) is MSCCLNopStep:
            raise Exception(f"Trying to add parent to Nop")
        if type(parent) is MSCCLReceiveReduceComputeStep:
            self.node.data_deps.append(parent.comp_node.id)
            return
        self.node.data_deps.append(parent.node.id)
    
    def encode_message(
        self,
        g
    ) -> None:
        encode_message(g, self.node)
    
class MSCCLCompStep(MSCCLStep):
    def __init__(
        self,
        tb_xml_node: ElementTree.Element,
        step_id: int,
        node_id: int, 
        comp_data_size_bytes: int
    ) -> None:
        tb_id = tb_xml_node.attrib['id']

        node = Node()
        node.id = node_id
        node.name = f"COMP_NODE_tb{tb_id}_step{step_id}"
        node.type = COMP_NODE
        # We do not fill in the compute duration because the data size is 
        # resolved within the simulator, not here.
        self.node = node


class MSCCLSendStep(MSCCLStep):
    def __init__(
        self,
        tb_xml_node: ElementTree.Element,
        step_id: int, 
        node_id: int,
        total_chunk_cnt: int,
        msg_chunk_cnt: int,
        msg_chunk_idx: int,
    ) -> None:
        tb_id = tb_xml_node.attrib['id']
        self.dst = int(tb_xml_node.attrib['send'])
        self.tag = int(tb_xml_node.attrib['chan'])

        node = Node()
        node.id = node_id
        node.name = f'COMM_SEND_NODE_tb{tb_id}_step{step_id}'
        node.type = COMM_SEND_NODE
        node.attr.append(ChakraAttr(name="comm_type",
                                    int64_val=COMM_SEND_NODE))
        node.attr.append(ChakraAttr(name="comm_dst",
                                    int32_val=self.dst))
        node.attr.append(ChakraAttr(name="comm_tag",
                                    int32_val=self.tag))
        node.attr.append(ChakraAttr(name="msg_chunk_cnt",
                                    int32_val=msg_chunk_cnt))
        node.attr.append(ChakraAttr(name="msg_chunk_idx",
                                    int32_val=msg_chunk_idx))
        node.attr.append(ChakraAttr(name="total_chunk_cnt",
                                    int32_val=total_chunk_cnt))
        self.node = node

class MSCCLReceiveStep(MSCCLStep):
    def __init__(
        self,
        tb_xml_node: ElementTree.Element,
        step_id: int, 
        node_id: int,
        total_chunk_cnt: int,
        msg_chunk_cnt: int,
        msg_chunk_idx: int,
    ) -> None:
        tb_id = tb_xml_node.attrib['id']
        self.src = int(tb_xml_node.attrib['recv'])
        self.tag = int(tb_xml_node.attrib['chan'])

        node = Node()
        node.id = node_id
        node.name = f'COMM_RECV_NODE_tb{tb_id}_step{step_id}'
        node.type = COMM_RECV_NODE
        node.attr.append(ChakraAttr(name="comm_type",
                                    int64_val=COMM_RECV_NODE))
        node.attr.append(ChakraAttr(name="comm_src",
                                    int32_val=self.src))
        node.attr.append(ChakraAttr(name="comm_tag",
                                    int32_val=self.tag))
        node.attr.append(ChakraAttr(name="msg_chunk_cnt",
                                    int32_val=msg_chunk_cnt))
        node.attr.append(ChakraAttr(name="msg_chunk_idx",
                                    int32_val=msg_chunk_idx))
        node.attr.append(ChakraAttr(name="total_chunk_cnt",
                                    int32_val=total_chunk_cnt))
        self.node = node

class MSCCLReceiveReduceComputeStep(MSCCLStep):
    def __init__(
        self,
        tb_xml_node: ElementTree.Element,
        step_id: int, 
        recv_node_id: int,
        comp_node_id: int,
        total_chunk_cnt: int,
        msg_chunk_cnt: int,
        msg_chunk_idx: int,
    ) -> None:
        tb_id = tb_xml_node.attrib['id']
        self.src = int(tb_xml_node.attrib['recv'])
        self.tag = int(tb_xml_node.attrib['chan'])

        recv_node = Node()
        recv_node.id = recv_node_id
        recv_node.name = f'COMM_RECV_NODE_tb{tb_id}_step{step_id}'
        recv_node.type = COMM_RECV_NODE
        recv_node.attr.append(ChakraAttr(name="comm_type",
                                    int64_val=COMM_RECV_NODE))
        recv_node.attr.append(ChakraAttr(name="comm_src",
                                    int32_val=self.src))
        recv_node.attr.append(ChakraAttr(name="comm_tag",
                                    int32_val=self.tag))
        recv_node.attr.append(ChakraAttr(name="msg_chunk_cnt",
                                    int32_val=msg_chunk_cnt))
        recv_node.attr.append(ChakraAttr(name="msg_chunk_idx",
                                    int32_val=msg_chunk_idx))
        recv_node.attr.append(ChakraAttr(name="total_chunk_cnt",
                                    int32_val=total_chunk_cnt))
        self.recv_node = recv_node

        comp_node = Node()
        comp_node.id = comp_node_id
        comp_node.name = f"COMP_NODE_tb{tb_id}_step{step_id}"
        comp_node.type = COMP_NODE
        comp_node.data_deps.append(recv_node.id)
        # We do not fill in the compute duration because the data size is 
        # resolved within the simulator, not here.
        self.comp_node = comp_node

    def encode_message(
        self,
        g
    ) -> None:
        encode_message(g, self.recv_node)
        encode_message(g, self.comp_node)

    def add_parent(
        self,
        parent: "MSCCLStep",
    ) -> None: 
        if type(parent) is MSCCLReceiveReduceComputeStep:
            self.recv_node.data_deps.append(parent.comp_node.id)
            return
        self.recv_node.data_deps.append(parent.node.id)

class MSCCLNopStep(MSCCLStep):
    def __init__(
        self,
    ) -> None:
        self.name = f"NOP_Node"

class MSCCL2ChakraConverter:
    def __init__(
        self,
        input_filename: str,
        output_filename: str,
        logger: logging.Logger
    ) -> None:
        self.input_filename = input_filename
        self.output_filename = output_filename
        self.logger = logger
        self.next_node_id = 0


    # Creates the global metadata info that is added to the start of all ET files.
    def create_global_metadata(self):
        input_text = ""
        with open(self.input_filename, "r") as input_file:
            input_text = input_file.read()
        attr = [
            ChakraAttr(name="schema", string_val="1.0.2-chakra.0.0.4"),
            ChakraAttr(name="input_file", string_val=input_text),
            ChakraAttr(name="collective", string_val=self.collective)
        ]
        metadata = GlobalMetadata(attr=attr)
        return metadata

    # Creates an ET node, and assigns a node id to it.
    # Increment the node id, to be assigned to the next ET node.
    def get_et_node_id(self) -> int:
        id = self.next_node_id
        self.next_node_id += 1
        return id

    # This function is called to reset the node id when starting to add nodes for a new ET trace file.
    # There will be one ET trace file for each NPU. 
    def reset_node_id(
            self
    ): self.next_node_id = 0

    # Add 'parent_node' as the parent to 'child_node'.
    # Note that parent_node and child_node has to be within the same ET trace file.
    def add_parent(
        self,
        child_node: Any,
        parent_node: Any
    ) -> None:
        child_node.data_deps.append(parent_node.id)
        
    def convert(self) -> None:
        node_map = {}
        step_map = {}
        tree = ElementTree.parse(self.input_filename)
        root = tree.getroot()

        collective = root.attrib['coll']
        if collective not in ["allreduce", "allgather", "alltoall", "reduce_scatter", "reduce", "broadcast"]:
            print(f"Error: Unsupported collective type {collective}")
            exit()
        self.collective = collective
        # Read the XML file and create ET Trace nodes. 
        for gpu in root.findall('gpu'):
            gpu_id = int(gpu.attrib['id'])
            total_chunk_cnt = int(gpu.attrib['i_chunks'])
            if total_chunk_cnt == 0:
                total_chunk_cnt = int(gpu.attrib['o_chunks'])
            node_map[gpu_id] = {}
            step_map[gpu_id] = {}
            self.reset_node_id()
            for tb in gpu.findall('tb'):
                tb_id = int(tb.attrib['id'])
                node_map[gpu_id][tb_id] = {}
                step_map[gpu_id][tb_id] = {}
                for step in tb.findall('step'):
                    step_id = int(step.attrib['s'])
                    msg_chunk_cnt = int(step.attrib['cnt'])
                    src_off = int(step.attrib['srcoff'])
                    dst_off = int(step.attrib['dstoff'])
                    if src_off != dst_off:
                        print(f"Error: At gpu {gpu_id} tb {tb_id} step {step} src_off {src_off} != dst_off {dst_off}")
                        exit()
                    msg_chunk_idx = src_off
                    step_map[gpu_id][tb_id][step_id] = step
                    et_node_id = self.get_et_node_id()
                    if step.attrib['type'] == "s":
                        node = MSCCLSendStep(tb, step_id, et_node_id, total_chunk_cnt, msg_chunk_cnt, msg_chunk_idx)
                        node_map[gpu_id][tb_id][step_id] = node
                    elif step.attrib['type'] == "r":
                        node = MSCCLReceiveStep(tb, step_id, et_node_id, total_chunk_cnt, msg_chunk_cnt, msg_chunk_idx)
                        node_map[gpu_id][tb_id][step_id] = node
                    elif step.attrib['type'] == "rrc":
                        comp_et_node_id = self.get_et_node_id()
                        node = MSCCLReceiveReduceComputeStep(tb, step_id, et_node_id, comp_et_node_id, total_chunk_cnt, msg_chunk_cnt, msg_chunk_idx)
                        node_map[gpu_id][tb_id][step_id] = node
                    elif step.attrib['type'] == "nop":
                        node = MSCCLNopStep()
                        node_map[gpu_id][tb_id][step_id] = node

        # For each ET Trace node, add the parent dependency information
        for gpu_id in node_map:
            for tb_id in node_map[gpu_id]:
                # Note that we're doing this in reverse order within a threadblock.
                for step_id, et_node in node_map[gpu_id][tb_id].items():
                    if type(et_node) is MSCCLNopStep:
                        continue
                    step = step_map[gpu_id][tb_id][step_id]
                    dep_tb_id = int(step.attrib['depid'])
                    dep_step_id = int(step.attrib['deps'])

                    # Parent by data dependency
                    if dep_tb_id != -1:
                        dep_node = node_map[gpu_id][dep_tb_id][dep_step_id]
                        try:
                            et_node.add_parent(dep_node)
                        except Exception as e:
                            print(e, f'{gpu_id}, {dep_tb_id}, {dep_tb_id}, {tb_id}, {step_id}')

                    # Parent by control
                    if step_id != 0:
                        prev_step_id = step_id -1
                        #print(gpu_id, tb_id, prev_step_id, step_id)
                        prev_node = node_map[gpu_id][tb_id][prev_step_id]
                        while type(prev_node) is MSCCLNopStep:
                            prev_step = step_map[gpu_id][tb_id][prev_step_id]
                            dep_tb_id = int(prev_step.attrib['depid'])
                            dep_step_id = int(prev_step.attrib['deps'])
                            dep_node = node_map[gpu_id][dep_tb_id][dep_step_id]
                            et_node.add_parent(dep_node)

                            prev_step_id = prev_step_id - 1
                            if prev_step_id < 0:
                                break
                            prev_node = node_map[gpu_id][tb_id][prev_step_id]
                        
                        if type(prev_node) is not MSCCLNopStep:
                            et_node.add_parent(prev_node)
        
        # For each ET Trace node, add the parent dependency information
        for gpu_id in node_map:
            output_filename = "%s.%s.et" % (self.output_filename, gpu_id)
            with open(output_filename, "wb") as g:
                global_metadata = self.create_global_metadata()
                encode_message(g, global_metadata)
                for tb_id in node_map[gpu_id]:
                    for step_id, et_node in node_map[gpu_id][tb_id].items():
                        if type(et_node) is MSCCLNopStep :
                            continue
                    
                        et_node.encode_message(g)
                        #if gpu_id == 0:
                            #print('encode node', et_node)
